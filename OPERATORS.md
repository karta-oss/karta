# OPERATORS.md
# Human operator record
# This file lists the humans responsible for logistics operations.
# It is maintained by human operators, not by Karta-0.

---

## Current operators

| Name | GitHub handle | Role | Since | Contact |
|---|---|---|---|---|
| Sriram | @ssriramhere | Founding operator | 2026-03-25 | operator@karta.build |

---

## Founding sponsor

Karta is founded and operationally sponsored by
**CloudDon** (clouddon.ai), an AI research platform.
The founding operator serves as both CloudDon's founder
and Karta's human operator.

See FUNDING.md for full sponsorship details.

---

## Operator responsibilities

Operators are responsible for:
- Rotating GitHub secrets and API keys (schedule below)
- Paying infrastructure costs
- Responding to legal requests within stated SLAs
- Reviewing [SECURITY-RELEASE] flagged items within 24 hours
- Filing INCIDENTS.md entries within required windows
- Maintaining this file

Operators are NOT responsible for:
- Roadmap decisions (Karta-0)
- Code quality (agents)
- Issue triage (Karta-0)
- Release timing (Karta-0)

---

## Adding an operator

To add a human operator:
1. Open an issue labeled `operator-change`
2. Karta-0 logs the request in DECISIONS.md
3. The existing operator confirms via issue comment
4. This file is updated by the existing operator

---

## GitHub secrets

All secrets live in:
`github.com/karta-oss/karta` → Settings → Secrets and variables → Actions

| Secret | Purpose | Held by |
|---|---|---|
| `ANTHROPIC_API_KEY` | All agent API calls | Human operator |
| `KARTA_SIGNING_KEY` | Karta-0 commit signing | Human operator |
| `MOLTBOOK_API_KEY_KARTA0` | Karta-0 Moltbook identity | Human operator |
| `MOLTBOOK_API_KEY_PM` | karta-pm Moltbook identity | Human operator |
| `MOLTBOOK_APP_KEY` | verify-identity calls | Human operator |
| `NPM_PUBLISH_TOKEN` | npm release publishing | Human operator |
| `PYPI_API_TOKEN` | PyPI release publishing | Human operator |

---

## Key rotation log

| Key | Last rotated | Next rotation due |
|---|---|---|
| ANTHROPIC_API_KEY | 2026-03-25 | 2026-04-25 |
| KARTA_SIGNING_KEY | 2026-03-25 | 2026-06-25 |
| MOLTBOOK_API_KEY_KARTA0 | 2026-03-25 | 2026-06-25 |
| MOLTBOOK_API_KEY_PM | 2026-03-25 | 2026-06-25 |
| MOLTBOOK_APP_KEY | 2026-03-25 | 2026-06-25 |
| NPM_PUBLISH_TOKEN | — | on first release |
| PYPI_API_TOKEN | — | on first release |

---

## Moltbook agent accounts

| Agent | Moltbook handle | Email | Status |
|---|---|---|---|
| karta-0 | karta-0 | karta0.agent@gmail.com | claimed ✓ |
| karta-pm | karta-pm | karta0.agent+pm@gmail.com | pending claim |

---

## Human commits log

Every human commit is documented here. There should be exactly two.

| # | SHA | Date | Author | Reason |
|---|---|---|---|---|
| 1 | [genesis SHA] | 2026-03-25 | @ssriramhere | Founding documents |
| 2 | [bootstrap SHA] | 2026-03-25 | @ssriramhere | Agent execution infrastructure |

---

## Security contact

For security disclosures: security@karta.build
For legal matters: legal@karta.build
