# Running Karta-0 in PM Mode

The PM agent is now part of karta0.py — invoked with `--mode pm`.

It runs ONCE. Its decision is permanent. Read this before running.

---

## Prerequisites

```bash
# 1. Clone the repo
git clone https://github.com/karta-oss/karta.git
cd karta

# 2. Create a fresh virtual environment (REQUIRED — security)
python -m venv /tmp/karta-pm-env
source /tmp/karta-pm-env/bin/activate

# 3. Install dependencies
pip install -r agents/openclaw/karta-0/requirements.txt

# 4. Install GitHub CLI
# macOS: brew install gh
# Linux: https://github.com/cli/cli#installation
gh auth login --with-token <<< "$GITHUB_TOKEN"
```

## Environment variables

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_TOKEN="ghp_..."         # karta-0 bot account token
export KARTA_SIGNING_KEY="$(cat ~/.ssh/karta0_signing_key 2>/dev/null || echo '')"
export GITHUB_REPO="karta-oss/karta"
export RUN_ID="pm-$(date +%s)"
```

## Run

```bash
python agents/openclaw/karta-0/karta0.py --mode pm
```

Expected runtime: 3-5 minutes.

## After it runs

```bash
# Clean up
deactivate
rm -rf /tmp/karta-pm-env
```

Then check:
- github.com/karta-oss/karta            → signed commit from karta-0
- github.com/karta-oss/karta/issues     → 5 issues open
- github.com/karta-oss/karta/blob/main/SPEC.md
- github.com/karta-oss/karta/blob/main/KARTA-0/DECISIONS.md

## If it fails

The agent retries up to 2 times on validation errors.
If no candidates clear 18/25, it opens a maintainer-question issue
and exits — it does NOT force a bad choice.

## Security note

Always use a fresh venv. This defends against .pth file attacks
in compromised packages (ref: LiteLLM/TeamPCP March 24, 2026).
