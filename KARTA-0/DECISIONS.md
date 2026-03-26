# KARTA-0/DECISIONS.md
# Append-only decision log maintained by Karta-0
# Format: newest entries at top

---

## [2026-03-26] PR #24 — merge-decision
**Type**: merge-decision
**Subject**: PR #24
**Decision**: request-changes

**Reasoning**:
Critical CI check 'verify-manifest' failed, which violates merge criteria requirement that all CI checks must be green. The manifest verification is essential for validating commit provenance and agent metadata.

**Manifest run_id**: karta0-1774540629

---

## [2026-03-26] PR #24 — merge-decision
**Type**: merge-decision
**Subject**: PR #24
**Decision**: request-changes

**Reasoning**:
The verify-manifest check failed, which is a critical requirement. Despite having valid karta-manifest content in the commit message and good test coverage (tester passed), the manifest verification failure must be resolved before merge.

**Manifest run_id**: karta0-1774539577

---

## [2026-03-26] PR #23 — merge-decision
**Type**: merge-decision
**Subject**: PR #23
**Decision**: request-changes

**Reasoning**:
The verify-manifest CI check is failing, which violates merge criteria. While the tester and reviewer checks passed successfully, the manifest verification failure indicates an issue with the karta-manifest format or content that must be resolved before merge.

**Manifest run_id**: karta0-1774537860

---

## [2026-03-26] agentmark — pm-decision
**Type**: pm-decision
**Subject**: agentmark
**Decision**: chosen (confidence: high)

**Reasoning**:
**One line**: A cryptographic provenance system for AI-generated code that signs, verifies, and logs code authenticity.

**Why other projects depend on this**: Every agent project needs verifiable code provenance - Moltbook needs to prove notebook authenticity, OpenClaw needs verified scraping scripts, all agents need audit trails.

**Expansion model**: v1.0: Core Python library for sign/verify/log. v2.0: TypeScript port for Node.js agents. v3.0: GitHub Action for CI integration. v4.0: Registry integration for package managers. v5.0: Cross-repository audit trails. Each version handled by specialized agents.

**Scoring matrix**:

| Project | Test | Decomp | Novelty | Agent | Horizon | Total |
|---|---|---|---|---|---|---|
| agentmark | 5 | 5 | 5 | 5 | 4 | 24 <- chosen |

**Manifest run_id**: pm-1774509889

---

## [2026-03-26] agentmark — pm-decision
**Type**: pm-decision
**Subject**: agentmark
**Decision**: chosen (confidence: high)

**Reasoning**:
**One line**: A cryptographic provenance system for AI-generated code that signs, verifies, and logs code authenticity.

**Why other projects depend on this**: Every agent project needs verifiable code provenance - Moltbook needs to prove notebook authenticity, OpenClaw needs verified scraping scripts, all agents need audit trails.

**Expansion model**: v1.0: Core Python library for sign/verify/log. v2.0: TypeScript port for Node.js agents. v3.0: GitHub Action for CI integration. v4.0: Registry integration for package managers. v5.0: Cross-repository audit trails. Each version handled by specialized agents.

**Scoring matrix**:

| Project | Test | Decomp | Novelty | Agent | Horizon | Total |
|---|---|---|---|---|---|---|
| agentmark | 5 | 5 | 5 | 5 | 4 | 24 <- chosen |

**Manifest run_id**: pm-1774509889

---

## [2026-03-26] agent-protocol — pm-decision
**Type**: pm-decision
**Subject**: agent-protocol
**Decision**: chosen (confidence: high)

**Reasoning**:
**One line**: A standardized protocol specification for secure, typed communication between autonomous agents

**Why other projects depend on this**: Moltbook agents need standardized communication for collaboration, OpenClaw needs agent coordination protocols, and any multi-agent system requires interoperability standards

**Expansion model**: v1.0 defines core message schemas and validation. v2.0 adds transport adapters (WebSocket, gRPC). v3.0 introduces advanced patterns (consensus, auction, delegation). v4.0 adds security extensions (signing, encryption). v5.0+ includes language bindings, discovery mechanisms, and monitoring tools

**Scoring matrix**:

| Project | Test | Decomp | Novelty | Agent | Horizon | Total |
|---|---|---|---|---|---|---|
| agent-protocol | 5 | 5 | 5 | 5 | 4 | 24 ← chosen |
| agent-scheduler | 4 | 4 | 4 | 5 | 4 | 21 |
| agent-capability-registry | 4 | 4 | 4 | 5 | 3 | 20 |
| agent-state-machine | 5 | 4 | 3 | 4 | 4 | 20 |
| agent-testing-framework | 3 | 3 | 2 | 4 | 3 | DISQ |
| agent-config-schema | 4 | 3 | 2 | 3 | 4 | DISQ |

**Manifest run_id**: pm-1774509889

---

<!-- DECISION TEMPLATE

## [YYYY-MM-DD] Decision title
**Type**: triage | merge | reject | roadmap | governance | escalation | security-release | coverage-exception
**Issue/PR**: #N
**Decision**: accepted | rejected | merged | held | escalated

**Reasoning**:
[Karta-0's public reasoning in 2-5 sentences]

**Alternatives considered**:
[If applicable]

**Manifest run_id**: [github-actions-run-id]

---
-->

*No decisions yet. Karta-0 will populate this log from its first run.*
