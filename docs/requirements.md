# Reference implementation obligations

| Requirement | Falsifiable acceptance threshold | Implementation | Witness |
| --- | --- | --- | --- |
| REQ-API-001 | Exactly the four named tools are discoverable over MCP; every response matches its output schema | server.py, results.py | test_stdio_protocol; isolated installed MCP smoke |
| REQ-CONTRACT-002 | Reject coercions, extra fields, duplicate IDs, unresolved references, invalid UTC, oversized records, and invalid envelopes | contract.py, encoding.py, server.py | test_contract.py; test_application_input_limit |
| REQ-EVIDENCE-003 | Missing/narrative/stale/inapplicable observations cannot establish success or runtime failure; hash mismatch/conflict causes HOLD | evidence.py, engine.py | test_missing_is_unknown; test_witness_validation; test_hash_blocker; test_conflicting_observations |
| REQ-DISPOSITION-004 | Exactly one primary disposition; HOLD and semantic drift cannot be erased by passing observations | engine.py | test_witnessed_failure; test_precedence_and_no_suppression |
| REQ-DELTA-005 | Every gap gets a stable ID, baseline reference, exact threshold, regression obligations, and no-promotion outcome | engine.py | test_requirement_identity_and_evidence_binding; test_mode_omission_is_not_hidden |
| REQ-AUTH-006 | Source paths/URLs remain inert; no target execution or I/O adapter in MCP implementation | server.py, evidence.py | test_source_reference_never_fetches; check_structure.py |
| REQ-REPORT-007 | Every graph edge resolves; complete declared nodes/edges and report views agree with JSON; injection cannot execute; mobile page does not overflow | graph.py, reports.py, data/report.* | test_reports.py; check_reports.py (nine real-browser cases) |
| REQ-REPLAY-008 | Identical contract/evaluator yields identical result across repeated and concurrent calls, with no cross-call evaluation state | engine.py, reports.py | test_replay_and_cross_call_isolation; test_graph_fidelity_and_machine_record |
| REQ-INSTALL-009 | Built wheel installs through uv; CLI, single skill, MCP, and bundled report templates work outside source imports | pyproject.toml, cli.py | verify_install.py |
| REQ-CLAIMS-010 | No outcome authorizes admission/certification; declared counts do not imply project coverage; internal artifacts excluded | results.py, SKILL.md, docs/threat-model.md | test_scoped_stability; release manifest; skill forward check |

| REQ-HOST-011 | All four shipped host profiles launch the isolated installed stdio server; all tools validate, malformed calls recover, replay survives changed calls and restart; CLI exits 0/2/3 and refuses overwrite | integrations/, check_connections.py, verify_install.py | evidence/connections.json; signed-in host UI acceptance remains unverified |

These are bounded reference-implementation requirements. Whole-project security, proof of execution authenticity, undeclared failure-mode discovery, causal delta measurement, and generalization remain outside the implemented claim.

## 0.1.1 bounded delta

Baseline: `14d519ad33cf30bb27e33b87c7d80cc4c5b6ff59` (0.1.0). The baseline
has a generic MCP configuration and installed smoke check, but no four-host
profile campaign. REQ-HOST-011 adds explicit configuration artifacts and installed
protocol/CLI witnesses. No public tool schema or evidence semantics change.
Regression obligations are all existing cumulative gates, unchanged skill bytes,
read-only annotations, deterministic replay, and the existing CLI contracts. If
the campaign fails, do not claim the profile validated. If a host client is absent,
retain that unverified status; do not infer signed-in host acceptance.
