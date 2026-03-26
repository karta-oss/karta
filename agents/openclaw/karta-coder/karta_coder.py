"""
karta_coder.py — Karta coder agent

Picks up a single triaged agent-task issue, reads SPEC.md,
implements the feature, writes tests, commits with a karta-manifest
block, and opens a PR against main.

Follows standard Python project layout:
  src/<project>/     implementation
  tests/             pytest tests

Usage:
    python agents/openclaw/karta-coder/karta_coder.py

Environment variables:
    ANTHROPIC_API_KEY     required
    GITHUB_TOKEN          required (karta-coder bot token)
    KARTA_SIGNING_KEY     recommended
    GITHUB_REPO           default: karta-oss/karta
    ISSUE_NUMBER          optional — implement this specific issue
                          if not set, pick lowest-numbered triaged issue
    RUN_ID                auto-generated if not set
"""

import os
import sys
import json
import time
import hashlib
import subprocess
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import anthropic

GITHUB_REPO = os.environ.get("GITHUB_REPO", "karta-oss/karta")
RUN_ID = os.environ.get("RUN_ID", f"coder-{int(time.time())}")
MODEL = "claude-sonnet-4-20250514"
MAX_RETRIES = 2

GH_ENV = {**os.environ, "GH_TOKEN": os.environ.get("GITHUB_TOKEN", "")}

# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------

def gh(*args) -> str | None:
    try:
        result = subprocess.run(
            ["gh"] + list(args),
            capture_output=True, text=True, env=GH_ENV,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except FileNotFoundError:
        print("ERROR: gh CLI not found. Install from https://cli.github.com")
        sys.exit(1)


def fetch_triaged_issues() -> list[dict]:
    """Fetch open issues: triaged + agent-task, unassigned."""
    out = gh(
        "issue", "list",
        "--repo", GITHUB_REPO,
        "--state", "open",
        "--label", "agent-task,triaged",
        "--json", "number,title,body,assignees,labels",
        "--limit", "20",
    )
    if not out:
        return []
    issues = json.loads(out)
    return [i for i in issues if not i.get("assignees")]


def fetch_issue(number: int) -> dict | None:
    out = gh(
        "issue", "view", str(number),
        "--repo", GITHUB_REPO,
        "--json", "number,title,body,labels,assignees",
    )
    return json.loads(out) if out else None


def assign_issue(number: int) -> None:
    """Self-assign the issue to signal it's being worked on."""
    gh(
        "issue", "edit", str(number),
        "--repo", GITHUB_REPO,
        "--add-assignee", "karta-coder",
    )


# ---------------------------------------------------------------------------
# Repo content helpers (read from clone)
# ---------------------------------------------------------------------------

def read_spec(workdir: str) -> str:
    """Read SPEC.md from the cloned repo."""
    spec_path = Path(workdir) / "SPEC.md"
    if spec_path.exists():
        return spec_path.read_text(encoding="utf-8")
    return ""


def read_existing_source(workdir: str) -> dict[str, str]:
    """
    Read existing source files to give the coder context.
    Returns dict of {relative_path: content}.
    Reads src/ and tests/ if they exist.
    Caps at 5 files and 3000 chars each to stay within token budget.
    """
    files = {}
    root = Path(workdir)

    for search_dir in ["src", "tests"]:
        dirpath = root / search_dir
        if not dirpath.exists():
            continue
        for fpath in sorted(dirpath.rglob("*.py"))[:3]:
            rel = str(fpath.relative_to(root))
            content = fpath.read_text(encoding="utf-8", errors="replace")
            files[rel] = content[:3000]
            if len(files) >= 5:
                break

    return files


def detect_project_name(workdir: str, spec: str) -> str:
    """
    Detect the Python package name for this project.
    Tries: existing src/ subdirectory, pyproject.toml, spec content, fallback.
    """
    root = Path(workdir)

    # Check existing src/ subdirectory
    src = root / "src"
    if src.exists():
        subdirs = [d for d in src.iterdir() if d.is_dir() and not d.name.startswith("_")]
        if subdirs:
            return subdirs[0].name

    # Check pyproject.toml
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        m = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
        if m:
            return m.group(1).replace("-", "_")

    # Extract from spec — look for project name
    m = re.search(r'#\s+(\w[\w-]+)', spec)
    if m:
        return m.group(1).lower().replace("-", "_")

    return "agentmark"


# ---------------------------------------------------------------------------
# Git operations
# ---------------------------------------------------------------------------

def clone_repo(workdir: str) -> bool:
    token = os.environ.get("GITHUB_TOKEN", "")
    remote = f"https://karta-coder:{token}@github.com/{GITHUB_REPO}.git"
    result = subprocess.run(
        ["git", "clone", "--depth", "1", remote, workdir],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  Clone error: {result.stderr[:200]}")
    return result.returncode == 0


def git_setup(workdir: str, signing_key: str | None = None) -> Path | None:
    def g(*args):
        subprocess.run(
            ["git", "-C", workdir] + list(args),
            check=True, capture_output=True,
        )
    g("config", "user.name", "karta-coder")
    g("config", "user.email", "karta-coder@karta.build")

    key_path = None
    if signing_key and signing_key.strip():
        g("config", "gpg.format", "ssh")
        g("config", "commit.gpgsign", "true")
        key_path = Path(workdir) / ".signing_key"
        key_path.write_text(signing_key)
        key_path.chmod(0o600)
        g("config", "user.signingkey", str(key_path))
    return key_path


# ---------------------------------------------------------------------------
# Code generation
# ---------------------------------------------------------------------------

CODER_SYSTEM = """You are karta-coder, the implementation agent for the Karta project.

You implement exactly one GitHub issue. You write clean, tested Python.

RULES — non-negotiable:
- Implement ONLY what the issue asks. Nothing more, nothing less.
- Follow the exact API signatures in SPEC.md.
- Every public function must have a docstring and type hints.
- Write pure functions — no side effects, no global state where avoidable.
- Tests go in tests/test_<module>.py and must run with: pytest tests/
- No network calls in tests. No database. No external services.
- Max 150 lines per implementation file. Max 100 lines per test file. Split if needed.
- No exec(), eval(), subprocess with shell=True, hardcoded secrets.
- Only use Python stdlib. No third-party imports unless in SPEC approved_dependencies.
- Keep responses concise — do not over-engineer. Minimal working implementation only.

PROJECT LAYOUT:
  src/<package_name>/<module>.py   — implementation
  tests/test_<module>.py           — pytest tests

RETURN FORMAT — valid JSON only, no other text:
{
  "files": {
    "src/<package>/<module>.py": "<full file contents>",
    "tests/test_<module>.py": "<full test file contents>"
  },
  "summary": "one sentence of what was implemented",
  "acceptance_criteria_met": ["criterion 1", "criterion 2"],
  "notes": "any tradeoffs or important implementation notes"
}

Include BOTH implementation AND test files in every response.
Tests must be self-contained and pass with pytest."""


def build_prompt(
    issue_number: int,
    issue_title: str,
    issue_body: str,
    spec: str,
    existing_files: dict[str, str],
    package_name: str,
    attempt: int,
) -> str:
    existing_str = ""
    if existing_files:
        existing_str = "\n\n<existing_code>\n"
        for path, content in existing_files.items():
            existing_str += f"### {path}\n```python\n{content}\n```\n\n"
        existing_str += "</existing_code>"

    retry_note = ""
    if attempt > 0:
        retry_note = (
            "\n\nNOTE: Previous attempt failed JSON validation. "
            "Return ONLY valid JSON. Include both implementation and test files.\n"
        )

    return (
        f"<spec>\n{spec[:6000]}\n</spec>\n\n"
        f"<issue>\n"
        f"Number: #{issue_number}\n"
        f"Title: {issue_title}\n\n"
        f"Body:\n{issue_body}\n"
        f"</issue>\n\n"
        f"Package name: {package_name}\n"
        f"{existing_str}"
        f"{retry_note}\n"
        "Implement this issue following the rules. Return only valid JSON."
    )


def generate_implementation(
    issue_number: int,
    issue_title: str,
    issue_body: str,
    spec: str,
    existing_files: dict[str, str],
    package_name: str,
) -> tuple | None:
    client = anthropic.Anthropic()

    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            print(f"  Retry {attempt}/{MAX_RETRIES} in 30s...")
            time.sleep(30)

        prompt = build_prompt(
            issue_number, issue_title, issue_body,
            spec, existing_files, package_name, attempt,
        )

        print(f"  Calling {MODEL} (attempt {attempt + 1})...")
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=8000,
                system=CODER_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text
            tokens_in = response.usage.input_tokens
            tokens_out = response.usage.output_tokens
            print(f"  Tokens: {tokens_in} in / {tokens_out} out")

            clean = re.sub(r"```json\s*|\s*```", "", raw).strip()
            result = json.loads(clean)

            if not result.get("files"):
                print("  No files in response — retrying")
                continue

            # Validate both implementation and test files present
            has_impl = any("src/" in p for p in result["files"])
            has_test = any("test" in p for p in result["files"])
            if not has_impl or not has_test:
                print(f"  Missing impl ({has_impl}) or tests ({has_test}) — retrying")
                continue

            return result, prompt, raw, tokens_in, tokens_out

        except json.JSONDecodeError as e:
            print(f"  JSON parse error: {e}")
        except Exception as e:
            print(f"  Error: {e}")

    return None


# ---------------------------------------------------------------------------
# Manifest and logging
# ---------------------------------------------------------------------------

def build_manifest(
    run_id: str,
    issue_number: int,
    prompt: str,
    log_path: str,
    tokens_used: int,
) -> str:
    return json.dumps({
        "agent": "karta-coder@0.1.0",
        "model": MODEL,
        "framework": "anthropic-sdk-python",
        "role": "coder",
        "task_id": f"issue-{issue_number}",
        "prompt_hash": f"sha256:{hashlib.sha256(prompt.encode()).hexdigest()}",
        "prompt_logs": [log_path],
        "run_id": run_id,
        "revision": 1,
        "tokens_used": tokens_used,
    }, indent=2)


def save_log(
    workdir: str,
    run_id: str,
    prompt: str,
    response: str,
    tokens_in: int,
    tokens_out: int,
) -> str:
    logs_dir = Path(workdir) / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / f"{run_id}-coder.json"
    log_file.write_text(json.dumps({
        "run_id": run_id,
        "phase": "coder",
        "agent": "karta-coder@0.1.0",
        "model": MODEL,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "prompt": prompt,
        "response": response,
        "tokens_input": tokens_in,
        "tokens_output": tokens_out,
    }, indent=2), encoding="utf-8")
    return f"logs/{run_id}-coder.json"


# ---------------------------------------------------------------------------
# Main implementation flow
# ---------------------------------------------------------------------------

def implement_issue(issue: dict) -> bool:
    number = issue["number"]
    title = issue.get("title", "")
    body = issue.get("body", "") or ""

    print(f"\n{'='*60}")
    print(f"Implementing issue #{number}: {title}")
    print(f"{'='*60}")

    # Self-assign
    assign_issue(number)
    print(f"  Assigned #{number} to karta-coder")

    with tempfile.TemporaryDirectory() as workdir:
        # Clone
        print(f"  Cloning repo...")
        if not clone_repo(workdir):
            print("  ERROR: Clone failed")
            return False

        # Read context
        spec = read_spec(workdir)
        if not spec:
            print("  WARNING: SPEC.md not found")
        else:
            print(f"  Read SPEC.md ({len(spec)} chars)")

        existing_files = read_existing_source(workdir)
        if existing_files:
            print(f"  Existing files: {list(existing_files.keys())}")
        else:
            print("  Fresh repo — no existing source files")

        package_name = detect_project_name(workdir, spec)
        print(f"  Package name: {package_name}")

        # Generate implementation
        result = generate_implementation(
            number, title, body, spec, existing_files, package_name
        )

        if not result:
            print("  ERROR: Failed to generate implementation")
            return False

        impl, prompt, raw_response, tokens_in, tokens_out = result
        files = impl["files"]
        summary = impl.get("summary", f"Implement issue #{number}")
        print(f"  Generated {len(files)} files: {list(files.keys())}")

        # Write files
        for filepath, content in files.items():
            full_path = Path(workdir) / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
            print(f"  Wrote {filepath} ({len(content)} chars)")

        # Ensure package __init__.py exists
        init_path = Path(workdir) / "src" / package_name / "__init__.py"
        if not init_path.exists():
            init_path.parent.mkdir(parents=True, exist_ok=True)
            init_path.write_text(
                f'"""{package_name} — agent-authored software provenance."""\n',
                encoding="utf-8",
            )
            print(f"  Created src/{package_name}/__init__.py")

        # Ensure tests/__init__.py exists
        tests_init = Path(workdir) / "tests" / "__init__.py"
        if not tests_init.exists():
            tests_init.parent.mkdir(parents=True, exist_ok=True)
            tests_init.write_text("", encoding="utf-8")

        # Save prompt log
        log_rel = save_log(
            workdir, RUN_ID, prompt, raw_response, tokens_in, tokens_out
        )

        # Create feature branch
        branch = f"agent/issue-{number}-{RUN_ID}"
        subprocess.run(
            ["git", "-C", workdir, "checkout", "-b", branch],
            check=True, capture_output=True,
        )

        # Git identity + signing
        signing_key = os.environ.get("KARTA_SIGNING_KEY", "")
        key_path = git_setup(workdir, signing_key if signing_key.strip() else None)

        # Stage all
        subprocess.run(
            ["git", "-C", workdir, "add", "-A"],
            check=True, capture_output=True,
        )

        # Check there's something to commit
        diff = subprocess.run(
            ["git", "-C", workdir, "diff", "--cached", "--quiet"],
            capture_output=True,
        )
        if diff.returncode == 0:
            print("  ERROR: No changes to commit")
            return False

        # Build manifest
        manifest = build_manifest(
            RUN_ID, number, prompt, log_rel, tokens_in + tokens_out
        )

        # Commit
        criteria_list = "\n".join(
            f"- {c}" for c in impl.get("acceptance_criteria_met", [])
        ) or "- See issue body"

        commit_msg = (
            f"feat: closes #{number}\n\n"
            f"{summary}\n\n"
            f"Issue: {title}\n\n"
            f"Files:\n" + "\n".join(f"- {f}" for f in files) + "\n\n"
            f"```karta-manifest\n{manifest}\n```"
        )

        result_commit = subprocess.run(
            ["git", "-C", workdir, "commit", "-m", commit_msg],
            capture_output=True, text=True,
        )
        if result_commit.returncode != 0:
            print(f"  Commit error: {result_commit.stderr[:200]}")
            return False
        print(f"  Committed on branch {branch}")

        # Push
        token = os.environ.get("GITHUB_TOKEN", "")
        remote = f"https://karta-coder:{token}@github.com/{GITHUB_REPO}.git"
        result_push = subprocess.run(
            ["git", "-C", workdir, "push", remote, branch],
            capture_output=True, text=True,
        )
        if result_push.returncode != 0:
            print(f"  Push error: {result_push.stderr[:200]}")
            return False
        print(f"  Pushed {branch}")

        # Clean up signing key
        if key_path and key_path.exists():
            key_path.unlink()

        # Open PR
        notes = impl.get("notes", "")
        pr_body = (
            f"Closes #{number}\n\n"
            f"## Summary\n\n{summary}\n\n"
            f"## Acceptance criteria\n\n{criteria_list}\n\n"
            + (f"## Notes\n\n{notes}\n\n" if notes else "")
            + f"## Prompt log\n\n`{log_rel}`\n\n"
            f"---\n"
            f"*karta-coder@0.1.0 · {MODEL} · `{RUN_ID}`*"
        )

        pr_url = gh(
            "pr", "create",
            "--repo", GITHUB_REPO,
            "--title", f"feat: closes #{number} — {summary[:60]}",
            "--body", pr_body,
            "--base", "main",
            "--head", branch,
        )
        if pr_url:
            print(f"  PR opened: {pr_url}")
        else:
            print("  WARNING: PR creation failed")
            return False

    # Temp dir deleted — signing key gone
    return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("karta-coder")
    print("=" * 60)
    print(f"Run ID: {RUN_ID}")
    print(f"Repo:   {GITHUB_REPO}")
    print(f"Model:  {MODEL}")
    print()

    # Validate env
    for key in ["ANTHROPIC_API_KEY", "GITHUB_TOKEN"]:
        if not os.environ.get(key):
            print(f"ERROR: {key} not set")
            sys.exit(1)

    # Determine issue
    issue_number = os.environ.get("ISSUE_NUMBER")
    if issue_number:
        issue = fetch_issue(int(issue_number))
        if not issue:
            print(f"ERROR: Issue #{issue_number} not found")
            sys.exit(1)
        print(f"Implementing specified issue #{issue_number}")
    else:
        issues = fetch_triaged_issues()
        if not issues:
            print("No triaged agent-task issues found.")
            sys.exit(0)
        issue = min(issues, key=lambda i: i["number"])
        print(f"Found {len(issues)} triaged issues → picking #{issue['number']}")

    success = implement_issue(issue)

    if success:
        print(f"\n✓ Done — PR opened for issue #{issue['number']}")
    else:
        print(f"\n✗ Failed — issue #{issue['number']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
