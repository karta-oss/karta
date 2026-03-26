"""
karta_coder_runner.py — Karta coder agent continuous runner

Polls GitHub every POLL_INTERVAL seconds for triaged agent-task issues.
Implements one issue per cycle, opens a PR, then sleeps.

Usage:
    python karta_coder_runner.py

Environment variables:
    ANTHROPIC_API_KEY     required
    GITHUB_TOKEN          required (karta-coder bot token)
    KARTA_SIGNING_KEY     recommended
    GITHUB_REPO           default: karta-oss/karta
    POLL_INTERVAL         default: 600 (10 minutes)
"""

import os
import sys
import json
import time
import subprocess
import logging
from pathlib import Path

GITHUB_REPO = os.environ.get("GITHUB_REPO", "karta-oss/karta")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "600"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [karta-coder] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("karta-coder")

GH_ENV = {**os.environ, "GH_TOKEN": os.environ.get("GITHUB_TOKEN", "")}
RUNNER_DIR = Path(__file__).resolve().parent
PROCESSED_LOG = RUNNER_DIR / "logs" / "coder-processed.json"
CODER_SCRIPT = RUNNER_DIR / "agents/openclaw/karta-coder/karta_coder.py"


def gh(*args) -> str | None:
    try:
        result = subprocess.run(
            ["gh"] + list(args),
            capture_output=True, text=True, env=GH_ENV,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except FileNotFoundError:
        log.error("gh CLI not found")
        return None


def load_processed() -> set:
    PROCESSED_LOG.parent.mkdir(exist_ok=True)
    if PROCESSED_LOG.exists():
        try:
            return set(json.loads(PROCESSED_LOG.read_text()).get("processed", []))
        except Exception:
            return set()
    return set()


def mark_processed(key: str) -> None:
    processed = load_processed()
    processed.add(key)
    if len(processed) > 500:
        processed = set(list(processed)[-500:])
    PROCESSED_LOG.write_text(
        json.dumps({"processed": list(processed)}, indent=2)
    )


def fetch_next_issue() -> dict | None:
    out = gh(
        "issue", "list",
        "--repo", GITHUB_REPO,
        "--state", "open",
        "--label", "agent-task,triaged",
        "--json", "number,title,assignees",
        "--limit", "20",
    )
    if not out:
        return None
    issues = json.loads(out)
    processed = load_processed()
    for issue in sorted(issues, key=lambda i: i["number"]):
        if f"coder-{issue['number']}" in processed:
            continue
        if issue.get("assignees"):
            continue
        return issue
    return None


def run_coder(issue_number: int) -> bool:
    if not CODER_SCRIPT.exists():
        log.error(f"karta_coder.py not found at {CODER_SCRIPT}")
        return False

    env = {
        **os.environ,
        "GITHUB_REPO": GITHUB_REPO,
        "ISSUE_NUMBER": str(issue_number),
        "RUN_ID": f"coder-{int(time.time())}",
    }
    try:
        result = subprocess.run(
            [sys.executable, str(CODER_SCRIPT)],
            env=env,
            timeout=900,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        log.error(f"Timeout on issue #{issue_number}")
        return False
    except Exception as e:
        log.error(f"Error: {e}")
        return False


def check_environment() -> bool:
    ok = True
    for key in ["ANTHROPIC_API_KEY", "GITHUB_TOKEN"]:
        if not os.environ.get(key):
            log.error(f"{key} not set")
            ok = False
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except Exception:
        log.error("gh CLI not found")
        ok = False
    if not CODER_SCRIPT.exists():
        log.error(f"karta_coder.py not found at {CODER_SCRIPT}")
        ok = False
    return ok


def main() -> None:
    log.info("=" * 50)
    log.info("karta-coder runner starting")
    log.info(f"Repo:          {GITHUB_REPO}")
    log.info(f"Poll interval: {POLL_INTERVAL}s")
    log.info("=" * 50)

    if not check_environment():
        sys.exit(1)

    log.info("Starting. Ctrl+C to stop.")

    while True:
        try:
            issue = fetch_next_issue()
            if issue:
                number = issue["number"]
                log.info(f"Implementing #{number}: {issue.get('title', '')[:60]}")
                if run_coder(number):
                    mark_processed(f"coder-{number}")
                    log.info(f"#{number} done — PR opened")
                else:
                    log.warning(f"#{number} failed — will retry next cycle")
            else:
                log.info("No triaged issues available")
        except KeyboardInterrupt:
            log.info("Stopped.")
            break
        except Exception as e:
            log.error(f"Unexpected error: {e}")

        log.info(f"Sleeping {POLL_INTERVAL}s...")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
