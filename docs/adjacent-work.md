# Adjacent work: Harness²

Primary sources, reviewed 2026-10-18:

- [Harness²: Recursive Agent Harnessing for an Open World](https://arxiv.org/html/2610.14224v1), Google Cloud AI Research and Northwestern University, dated 2026-10-09.
- [Google Research reference repository](https://github.com/google-research/harness2).
- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x).
- [MCP tool specification](https://modelcontextprotocol.io/specification/2025-11-25/server/tools).

Harness² proposes, probes, and composes harness changes, then retains supported experience. Its behavioral comparisons use matched model/environment conditions; the paper distinguishes contrastive evidence from correctness and selection from proof of transferability. This project evaluates supplied evidence and derives obligations; it does not execute that improvement loop.

The following are design recommendations inferred for this use case:

| Gap to challenge | Public method response | v1 implementation status |
| --- | --- | --- |
| A plausible edit has no measurable benefit | Require baseline/candidate observations and an explicit acceptance threshold | Skill obligation; no automatic candidate comparison |
| A local gain weakens another invariant | Keep regression and blocking obligations visible | Required modes, precedence, and requirement regression links |
| A reusable lesson silently imports stale context | Revalidate baseline, environment, time, and scope | Context/freshness checks; no persistent lesson store |
| Repeated agreement is mistaken for correctness | Require an independently governed expected observation | Expected/actual separation; no producer authentication |
| Search budget or judge bias is hidden | State uncontrolled variables and unavailable independent verifiers | Explicit limitations; no statistical inference |

No code or benchmark corpus from Harness² is included. No novelty, priority, comparative performance, endorsement, or security certification is claimed.
