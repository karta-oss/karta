"""
manifest.py — Karta commit manifest validator

Used by verify-manifest.yml CI workflow to reject commits
missing or malforming the karta-manifest or agentmark-manifest block.

Usage:
    python agents/openclaw/manifest.py --verify
    python agents/openclaw/manifest.py --verify-range origin/main..HEAD --strict
    python agents/openclaw/manifest.py --verify-logs origin/main..HEAD
"""

import sys
import json
import re
import subprocess
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = REPO_ROOT / "logs"

# Legacy karta-manifest required fields
KARTA_REQUIRED_FIELDS = [
    "agent",
    "model",
    "framework",
    "role",
    "task_id",
    "prompt_hash",
    "run_id",
    "revision",
    "tokens_used",
]

# agentmark-manifest required fields
AGENTMARK_REQUIRED_FIELDS = [
    "version",
    "provider",
    "model",
    "output_hash",
    "challenge_token",
    "pipeline_key",
    "timestamp",
    "signature",
]

VALID_ROLES = {
    "coder",
    "tester",
    "reviewer",
    "doc-writer",
    "dep-reviewer",
    "karta-0",
}

# Legacy karta-manifest pattern
KARTA_MANIFEST_PATTERN = re.compile(
    r"```karta-manifest\s*(\{.*?\})\s*```",
    re.DOTALL,
)

# agentmark-manifest pattern
AGENTMARK_MANIFEST_PATTERN = re.compile(
    r"```agentmark-manifest\s*(\{.*?\})\s*```",
    re.DOTALL,
)


def extract_manifest(commit_message: str) -> tuple[dict | None, str]:
    """
    Extract and parse manifest from commit message.
    Returns (manifest_dict, manifest_type) where type is
    'agentmark', 'karta', or None.
    """
    # Try agentmark-manifest first (preferred)
    match = AGENTMARK_MANIFEST_PATTERN.search(commit_message)
    if match:
        try:
            return json.loads(match.group(1)), "agentmark"
        except json.JSONDecodeError:
            return None, "agentmark"

    # Fall back to legacy karta-manifest
    match = KARTA_MANIFEST_PATTERN.search(commit_message)
    if match:
        try:
            return json.loads(match.group(1)), "karta"
        except json.JSONDecodeError:
            return None, "karta"

    return None, None


def validate_agentmark_manifest(manifest: dict) -> list[str]:
    """Validate an agentmark-manifest block."""
    errors = []

    for field in AGENTMARK_REQUIRED_FIELDS:
        if field not in manifest or not manifest[field]:
            errors.append(f"Missing required field: {field}")

    if "output_hash" in manifest:
        if not manifest["output_hash"].startswith("sha256:"):
            errors.append("output_hash must start with 'sha256:'")

    if "challenge_token" in manifest:
        if not manifest["challenge_token"].startswith("agentmark-"):
            errors.append("challenge_token must start with 'agentmark-'")

    return errors


def validate_karta_manifest(manifest: dict) -> list[str]:
    """Validate a legacy karta-manifest block."""
    errors = []

    for field in KARTA_REQUIRED_FIELDS:
        if field not in manifest:
            errors.append(f"Missing required field: {field}")

    has_prompt_log = (
        "prompt_log" in manifest or "prompt_logs" in manifest
    )
    if not has_prompt_log:
        errors.append("Missing required field: prompt_log (or prompt_logs)")

    if "role" in manifest and manifest["role"] not in VALID_ROLES:
        errors.append(
            f"Invalid role '{manifest['role']}'. "
            f"Must be one of: {', '.join(sorted(VALID_ROLES))}"
        )

    if "prompt_hash" in manifest:
        if not manifest["prompt_hash"].startswith("sha256:"):
            errors.append("prompt_hash must start with 'sha256:'")

    if "revision" in manifest:
        if not isinstance(manifest["revision"], int) or manifest["revision"] < 1:
            errors.append("revision must be a positive integer")

    if "tokens_used" in manifest:
        if not isinstance(manifest["tokens_used"], int) or manifest["tokens_used"] < 0:
            errors.append("tokens_used must be a non-negative integer")

    return errors


def validate_manifest(manifest: dict, manifest_type: str) -> list[str]:
    """Dispatch to correct validator based on manifest type."""
    if manifest_type == "agentmark":
        return validate_agentmark_manifest(manifest)
    return validate_karta_manifest(manifest)


def get_commits_in_range(commit_range: str) -> list[tuple[str, str]]:
    """Return list of (sha, message) for commits in range."""
    result = subprocess.run(
        ["git", "log", "--format=%H%x00%B%x00---COMMIT_END---", commit_range],
        capture_output=True,
        text=True,
        check=True,
    )
    commits = []
    for chunk in result.stdout.split("---COMMIT_END---"):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split("\x00", 1)
        if len(parts) == 2:
            sha, message = parts
            commits.append((sha.strip(), message.strip()))
    return commits


def verify_single_commit() -> bool:
    """Verify the HEAD commit has a valid manifest."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%B"],
        capture_output=True,
        text=True,
        check=True,
    )
    message = result.stdout.strip()
    manifest, manifest_type = extract_manifest(message)

    if manifest is None:
        print("ERROR: No manifest block found in commit message")
        print("Every commit must include either:")
        print("  - ```agentmark-manifest {...} ``` (preferred)")
        print("  - ```karta-manifest {...} ``` (legacy)")
        return False

    errors = validate_manifest(manifest, manifest_type)
    if errors:
        print(f"ERROR: Invalid {manifest_type}-manifest:")
        for e in errors:
            print(f"  - {e}")
        return False

    if manifest_type == "agentmark":
        print(f"✓ agentmark-manifest valid — pipeline: {manifest.get('pipeline_key')}, provider: {manifest.get('provider')}")
    else:
        print(f"✓ karta-manifest valid — agent: {manifest.get('agent')}, role: {manifest.get('role')}")
    return True


def verify_range(commit_range: str, strict: bool = False) -> bool:
    """Verify all commits in range have valid manifests."""
    commits = get_commits_in_range(commit_range)

    if not commits:
        print("No commits found in range")
        return True

    all_valid = True
    for sha, message in commits:
        short_sha = sha[:8]

        # Skip merge commits
        if message.startswith("Merge "):
            print(f"  {short_sha} — merge commit, skipping")
            continue

        # Skip operator infrastructure commits
        operator_prefixes = ("fix:", "chore:", "docs:", "ci:", "refactor:", "test:")
        if any(message.startswith(p) for p in operator_prefixes):
            print(f"  {short_sha} — operator commit, skipping")
            continue

        manifest, manifest_type = extract_manifest(message)

        if manifest is None:
            if strict:
                print(f"  {short_sha} ERROR: No manifest found")
                all_valid = False
            else:
                print(f"  {short_sha} WARNING: No manifest found")
            continue

        errors = validate_manifest(manifest, manifest_type)
        if errors:
            print(f"  {short_sha} ERROR: Invalid {manifest_type}-manifest:")
            for e in errors:
                print(f"    - {e}")
            all_valid = False
        else:
            if manifest_type == "agentmark":
                print(
                    f"  {short_sha} ✓ agentmark / "
                    f"{manifest.get('pipeline_key')} / "
                    f"{manifest.get('provider')} / "
                    f"{manifest.get('model')}"
                )
            else:
                print(
                    f"  {short_sha} ✓ {manifest.get('agent')} / "
                    f"{manifest.get('role')} / {manifest.get('task_id')}"
                )

    return all_valid


def verify_logs(commit_range: str) -> bool:
    """Verify that prompt log files exist for commits with karta-manifest."""
    commits = get_commits_in_range(commit_range)
    all_valid = True

    for sha, message in commits:
        short_sha = sha[:8]

        if message.startswith("Merge "):
            continue

        manifest, manifest_type = extract_manifest(message)
        if manifest is None:
            continue

        # agentmark manifests have prompt_log as optional
        if manifest_type == "agentmark":
            log_path = manifest.get("prompt_log")
            if not log_path:
                print(f"  {short_sha} — agentmark manifest, no prompt_log (optional)")
                continue
        else:
            log_path = manifest.get("prompt_log")
            if not log_path:
                print(f"  {short_sha} ERROR: No prompt_log in manifest")
                all_valid = False
                continue

        full_path = REPO_ROOT / log_path
        if not full_path.exists():
            print(f"  {short_sha} ERROR: Log file not found: {log_path}")
            all_valid = False
        else:
            print(f"  {short_sha} ✓ Log exists: {log_path}")

    return all_valid


def main() -> None:
    parser = argparse.ArgumentParser(description="Karta manifest validator")
    parser.add_argument("--verify", action="store_true", help="Verify HEAD commit")
    parser.add_argument("--verify-range", help="Verify commits in git range")
    parser.add_argument(
        "--strict", action="store_true", help="Fail on missing manifests"
    )
    parser.add_argument("--verify-logs", help="Verify prompt logs exist for range")
    args = parser.parse_args()

    if args.verify:
        ok = verify_single_commit()
        sys.exit(0 if ok else 1)

    if args.verify_range:
        ok = verify_range(args.verify_range, strict=args.strict)
        sys.exit(0 if ok else 1)

    if args.verify_logs:
        ok = verify_logs(args.verify_logs)
        sys.exit(0 if ok else 1)

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
