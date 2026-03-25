# OPERATORS.md
# Human operator record
# This file lists the humans responsible for logistics operations.
# It is maintained by human operators, not by Karta-0.

---

## Current operators

| Name | GitHub handle | Role | Since | Contact |
|---|---|---|---|---|
| Sriram | @ssriramhere | Founding operator | 2026-03-24 | operator@karta.build |

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
- Rotating GitHub secrets and API keys (every 30 days)
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

## Key rotation log

| Key | Last rotated | Next rotation due |
|---|---|---|
| ANTHROPIC_API_KEY | 2026-03-24 | 2026-04-24 |
| KARTA_SIGNING_KEY | 2026-03-24 | 2026-06-24 |
| NPM_PUBLISH_TOKEN | — | on first release |
| PYPI_API_TOKEN | — | on first release |
| MOLTBOOK_APP_KEY | — | on first release |

---

## Security contact

For security disclosures: security@karta.build
For legal matters: legal@karta.build
