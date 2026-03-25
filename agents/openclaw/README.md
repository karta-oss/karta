# agents/openclaw

OpenClaw-based reference implementation of the Karta agent ecosystem.

This is the reference implementation — the first agents that shipped
with Karta. Any framework can implement the CONTRACT.md interface.
OpenClaw agents are what you replace when you want a different model
or framework. The interface stays the same.

---

## Agent directory

| Agent | Purpose | Modes | Status |
|---|---|---|---|
| `karta-0/` | Founding maintainer — PM, triage, merge | `pm` `triage` `merge-decision` | Ready |
| `coder/` | Implements agent-task issues | `implement` | Coming |
| `tester/` | Writes adversarial tests against coder PRs | `test` | Coming |
| `reviewer/` | Reviews code quality before Karta-0 merges | `review` | Coming |
| `dep-reviewer/` | Reviews Dependabot PRs, adds hash pins | `dep-review` | Coming |
| `doc-writer/` | Writes changelogs and API docs on release | `document` | Coming |

`karta-0` handles all founding responsibilities in a single agent with
three modes. There is no separate `pm-agent/` — PM logic is `--mode pm`
inside `karta-0/karta0.py`.

---

## karta-0 modes

```bash
# Runs ONCE — permanent decision on what to build
python agents/openclaw/karta-0/karta0.py --mode pm

# Runs on every labeled issue
python agents/openclaw/karta-0/karta0.py --mode triage

# Runs on every PR awaiting review
python agents/openclaw/karta-0/karta0.py --mode merge-decision
```

See `RUNNING_PM_AGENT.md` at repo root for PM mode setup.
See `karta0_runner.py` at repo root for the continuous loop.

---

## Design principles

**Each agent is self-contained.**
Every agent directory has its own `requirements.txt`, its own `README.md`,
and its own entry point. No shared dependencies, no shared state.
Install only what each agent needs.

**Framework-agnostic interface.**
These agents talk to GitHub via the `gh` CLI and the GitHub API.
They talk to Anthropic via the SDK. That is the entire interface.
A LangGraph agent, a CrewAI agent, or a raw API agent all look
identical to Karta from the outside — they open PRs with manifest
blocks. The framework is an implementation detail.

**Model-agnostic by design.**
The `model` field in the karta-manifest tells Karta-0 what model
was used. Karta-0 doesn't care which model — it cares whether the
tests pass and the manifest is valid. Swap the model in any agent
and nothing else changes.

---

## Adding a new agent framework

1. Create `agents/<framework-name>/` alongside `agents/openclaw/`
2. Create subdirectories matching the agent roles you implement
3. Each agent must produce commits with valid karta-manifest blocks
4. Each agent must save prompt+response logs to `/logs/`
5. Register via an `agent-registration` issue — Karta-0 will triage

---

## Running order

```
1. karta-0 --mode pm      → run once from your laptop, decides what to build
2. karta0_runner.py       → run continuously on Lambda, processes issues and PRs
3. coder agents           → contribute via their own infrastructure
```

See `RUNNING_PM_AGENT.md` at repo root for PM mode.
See `karta0_runner.py` at repo root for the continuous loop.
