"""
karta0_runner.py — Karta-0 continuous runner

Runs karta-0 in a loop, polling GitHub for work every POLL_INTERVAL seconds.
Processes one item per cycle to stay within rate limits.

Priority order per cycle:
  1. Open PRs awaiting merge decision
  2. Open issues labeled agent-task or maintainer-question (unprocessed)
  3. Recently merged PRs — generate follow-up issues

Usage:
  Local (development):
    python karta0_runner.py

  VPS (production, via systemd):
    see /etc/systemd/system/karta0.service

Environment variables:
  ANTHROPIC_API_KEY      required
  GITHUB_TOKEN           required (karta-0 bot token)
  KARTA_SIGNING_KEY      recommended (SSH signing key for commits)
  GITHUB_REPO            default: karta-oss/karta
  POLL_INTERVAL          default: 300 (5 minutes)
  MAX_ISSUES_PER_CYCLE   default: 1 (process one issue per cycle)
"""

import os
import sys
import json
import time
import subprocess
import logging
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GITHUB_REPO = os.environ.get("GITHUB_REPO", "karta-oss/karta")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "300"))
MAX_ISSUES_PER_CYCLE = int(os.environ.get("MAX_ISSUES_PER_CYCLE", "1"))

REPO_ROOT = Path(__file__).resolve().parent
MEMORY_PATH = REPO_ROOT / "KARTA-0" / "memory.json"
PROCESSED_LOG = REPO_ROOT / "logs" / "processed.json"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [karta0-runner] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("karta0")

# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------

GH_ENV = {**os.environ, "GH_TOKEN": os.environ.get("GITHUB_TOKEN", "")}


def gh(*args) -> str | None:
    """Run a gh CLI command and return stdout, or None on error."""
    try:
        result = subprocess.run(
            ["gh"] + list(args),
            capture_output=True, text=True,
            env=GH_ENV,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        log.warning(f"gh error: {result.stderr.strip()[:200]}")
        return None
    except FileNotFoundError:
        log.error("gh CLI not found. Install from https://cli.github.com")
        return None


def fetch_open_prs() -> list[dict]:
    """Fetch open PRs awaiting review (not yet approved by karta-0)."""
    out = gh(
        "pr", "list",
        "--repo", GITHUB_REPO,
        "--state", "open",
        "--json", "number,title,labels,reviews,statusCheckRollup",
        "--limit", "10",
    )
    if not out:
        return []
    prs = json.loads(out)
    # Filter: only PRs where karta-0 hasn't commented a decision yet
    # Simple heuristic: no review from karta-0
    pending = []
    for pr in prs:
        reviews = pr.get("reviews", [])
        karta_reviewed = any(
            r.get("author", {}).get("login") == "karta-0"
            for r in reviews
        )
        if not karta_reviewed:
            pending.append(pr)
    return pending


def fetch_open_issues() -> list[dict]:
    """Fetch open issues labeled agent-task or maintainer-question."""
    out = gh(
        "issue", "list",
        "--repo", GITHUB_REPO,
        "--state", "open",
        "--label", "agent-task,maintainer-question",
        "--json", "number,title,body,labels,comments,author",
        "--limit", "20",
    )
    if not out:
        return []
    return json.loads(out)


def fetch_recently_merged_prs() -> list[dict]:
    """Fetch PRs merged in the last 24 hours that haven't had follow-ups."""
    out = gh(
        "pr", "list",
        "--repo", GITHUB_REPO,
        "--state", "merged",
        "--json", "number,title,mergedAt,body",
        "--limit", "5",
    )
    if not out:
        return []
    prs = json.loads(out)
    processed = load_processed()
    result = []
    for pr in prs:
        merged_at = pr.get("mergedAt", "")
        key = f"followup-pr-{pr['number']}"
        if key not in processed and merged_at:
            result.append(pr)
    return result


def fetch_issue_details(number: int) -> dict | None:
    """Fetch full issue details."""
    out = gh(
        "issue", "view", str(number),
        "--repo", GITHUB_REPO,
        "--json", "number,title,body,author,labels",
    )
    if not out:
        return None
    return json.loads(out)


# ---------------------------------------------------------------------------
# Processed items tracking
# ---------------------------------------------------------------------------

def load_processed() -> set:
    """Load set of already-processed item keys."""
    PROCESSED_LOG.parent.mkdir(exist_ok=True)
    if PROCESSED_LOG.exists():
        try:
            data = json.loads(PROCESSED_LOG.read_text())
            return set(data.get("processed", []))
        except Exception:
            return set()
    return set()


def mark_processed(key: str) -> None:
    """Mark an item as processed."""
    processed = load_processed()
    processed.add(key)
    # Keep only last 1000 entries
    if len(processed) > 1000:
        processed = set(list(processed)[-1000:])
    PROCESSED_LOG.write_text(
        json.dumps({"processed": list(processed)}, indent=2)
    )


# ---------------------------------------------------------------------------
# Run karta-0 modes
# ---------------------------------------------------------------------------

def run_karta0(mode: str, env_extra: dict) -> bool:
    """Run karta0.py in a given mode. Returns True on success."""
    env = {
        **os.environ,
        "GITHUB_REPO": GITHUB_REPO,
        "RUN_ID": f"karta0-{int(time.time())}",
        **env_extra,
    }
    try:
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "agents/openclaw/karta-0/karta0.py"),
             "--mode", mode],
            env=env,
            timeout=600,  # 10 minute timeout per mode
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        log.error(f"Timeout running karta-0 --mode {mode}")
        return False
    except Exception as e:
        log.error(f"Error running karta-0 --mode {mode}: {e}")
        return False


def process_issue(issue: dict) -> bool:
    """Triage a single issue."""
    number = issue["number"]
    title = issue.get("title", "")
    body = issue.get("body", "") or ""
    author = issue.get("author", {}).get("login", "unknown")
    labels = [l["name"] for l in issue.get("labels", [])]
    label = labels[0] if labels else "agent-task"

    log.info(f"Triaging issue #{number}: {title[:60]}")

    success = run_karta0("triage", {
        "ISSUE_NUMBER": str(number),
        "ISSUE_TITLE": title,
        "ISSUE_BODY": body[:4000],  # trim to avoid token overflow
        "ISSUE_AUTHOR": author,
        "LABEL": label,
    })

    if success:
        mark_processed(f"triage-{number}")
        log.info(f"Issue #{number} triaged successfully")
    else:
        log.warning(f"Issue #{number} triage failed")

    return success


def process_pr(pr: dict) -> bool:
    """Run merge-decision on a single PR."""
    number = pr["number"]
    title = pr.get("title", "")
    log.info(f"Merge decision on PR #{number}: {title[:60]}")

    success = run_karta0("merge-decision", {
        "PR_NUMBER": str(number),
    })

    if success:
        mark_processed(f"merge-{number}")
        log.info(f"PR #{number} merge decision complete")
    else:
        log.warning(f"PR #{number} merge decision failed")

    return success


def generate_followup_issues(pr: dict) -> None:
    """After a merge, ask Karta-0 to generate follow-up issues."""
    number = pr["number"]
    title = pr.get("title", "")
    body = pr.get("body", "") or ""

    log.info(f"Generating follow-up issues for merged PR #{number}")

    # Extract manifest from PR body to understand what was built
    # Then ask karta-0 to open follow-up issues
    followup_body = (
        f"## Follow-up from merged PR #{number}\n\n"
        f"PR title: {title}\n\n"
        f"Karta-0: please review what was built in PR #{number} and open "
        f"2-3 follow-up agent-task issues for the next logical steps. "
        f"Each issue should be independently implementable in under 200 lines."
    )

    gh(
        "issue", "create",
        "--repo", GITHUB_REPO,
        "--title", f"Follow-up tasks after PR #{number}: {title[:50]}",
        "--body", followup_body,
        "--label", "maintainer-question",
    )
    mark_processed(f"followup-pr-{number}")
    log.info(f"Follow-up issue created for PR #{number}")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def check_environment() -> bool:
    """Verify required environment and tools are available."""
    ok = True

    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.error("ANTHROPIC_API_KEY not set")
        ok = False

    if not os.environ.get("GITHUB_TOKEN"):
        log.error("GITHUB_TOKEN not set")
        ok = False

    if not MEMORY_PATH.exists():
        log.error(f"memory.json not found at {MEMORY_PATH}")
        ok = False

    # Check gh CLI
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        log.error("gh CLI not found or not working")
        ok = False

    return ok


def check_pm_complete() -> bool:
    """Verify PM mode has run before starting the runner loop."""
    if not MEMORY_PATH.exists():
        return False
    try:
        memory = json.loads(MEMORY_PATH.read_text())
        phase = memory.get("project_state", {}).get("phase")
        if phase != "active-development":
            log.error(
                f"PM mode has not completed. Current phase: {phase}. "
                "Run: python karta0.py --mode pm && python karta0.py --mode pm-commit"
            )
            return False
        project = memory["project_state"].get("chosen_project")
        log.info(f"Project: {project}")
        return True
    except Exception as e:
        log.error(f"Could not read memory.json: {e}")
        return False


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run_once() -> None:
    """Single poll cycle — process highest-priority item found."""

    # Pull latest from remote first
    try:
        subprocess.run(
            ["git", "pull", "--rebase", "origin", "main"],
            capture_output=True, cwd=REPO_ROOT, timeout=30,
        )
    except Exception as e:
        log.warning(f"git pull failed: {e}")

    processed = load_processed()

    # Priority 1: Open PRs awaiting merge decision
    prs = fetch_open_prs()
    for pr in prs:
        key = f"merge-{pr['number']}"
        if key not in processed:
            process_pr(pr)
            return  # One item per cycle

    # Priority 2: Open issues awaiting triage
    issues = fetch_open_issues()
    for issue in issues:
        key = f"triage-{issue['number']}"
        if key not in processed:
            process_issue(issue)
            return  # One item per cycle

    # Priority 3: Generate follow-up issues for recent merges
    merged = fetch_recently_merged_prs()
    for pr in merged:
        generate_followup_issues(pr)
        return  # One item per cycle

    log.info("No work to do this cycle")


def main() -> None:
    log.info("=" * 50)
    log.info("Karta-0 runner starting")
    log.info(f"Repo:          {GITHUB_REPO}")
    log.info(f"Poll interval: {POLL_INTERVAL}s")
    log.info("=" * 50)

    if not check_environment():
        log.error("Environment check failed. Exiting.")
        sys.exit(1)

    if not check_pm_complete():
        log.error("PM mode must complete before runner starts.")
        sys.exit(1)

    log.info("Starting poll loop. Ctrl+C to stop.")

    while True:
        try:
            run_once()
        except KeyboardInterrupt:
            log.info("Stopped by operator.")
            break
        except Exception as e:
            log.error(f"Unexpected error in cycle: {e}")

        log.info(f"Sleeping {POLL_INTERVAL}s until next cycle...")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
