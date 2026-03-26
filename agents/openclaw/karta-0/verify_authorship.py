"""
verify_authorship.py — Karta human commit detector

Scans a git commit range and fails if any commit was authored
by an account not in the allowed bot accounts list.

Usage:
    python agents/openclaw/verify_authorship.py \
        --range origin/main..HEAD \
        --allowed-bot-accounts "karta-0,dependabot[bot]"
"""

import sys
import subprocess
import argparse


def get_commit_authors(commit_range: str) -> list[tuple[str, str, str]]:
    """Return list of (sha, author_name, author_email) for commits in range."""
    result = subprocess.run(
        ["git", "log", "--format=%H%x00%an%x00%ae", commit_range],
        capture_output=True,
        text=True,
        check=True,
    )
    authors = []
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        parts = line.split("\x00")
        if len(parts) == 3:
            authors.append((parts[0][:8], parts[1], parts[2]))
    return authors


def verify_authorship(commit_range: str, allowed_accounts: list[str]) -> bool:
    """Return True if all commits in range are by allowed bot accounts."""
    commits = get_commit_authors(commit_range)

    if not commits:
        print("No commits found in range")
        return True

    allowed_lower = [a.lower() for a in allowed_accounts]
    all_valid = True

    for sha, name, email in commits:
        name_lower = name.lower()
        email_lower = email.lower()

        is_allowed = any(
            allowed in name_lower or allowed in email_lower
            for allowed in allowed_lower
        )

        if is_allowed:
            print(f"  {sha} ✓ {name} <{email}>")
        else:
            print(
                f"  {sha} ERROR: Human commit detected — "
                f"{name} <{email}> is not in the allowed bot accounts list"
            )
            all_valid = False

    if not all_valid:
        print("\nVIOLATION: Human-authored commits found.")
        print("Karta's contract requires all commits to be authored by agents.")
        print("See AGENTS.md for the project rules.")

    return all_valid


def main() -> None:
    parser = argparse.ArgumentParser(description="Karta authorship verifier")
    parser.add_argument("--range", required=True, help="Git commit range to check")
    parser.add_argument(
        "--allowed-bot-accounts",
        required=True,
        help="Comma-separated list of allowed bot account names",
    )
    args = parser.parse_args()

    allowed = [a.strip() for a in args.allowed_bot_accounts.split(",")]
    print(f"Checking authorship for range: {args.range}")
    print(f"Allowed accounts: {allowed}")

    ok = verify_authorship(args.range, allowed)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
