# Evaluation contract v1.0

`hmt-mission-assurance schema` emits the authoritative input JSON Schema generated from `EvaluationContract`. `schemas/evaluation-contract.schema.json` is a checked-in generated view; CI checks parity. All four MCP tools use the same `ToolRequest` envelope containing exactly `contract`.

| Surface | Contract |
| --- | --- |
| Scope | One tool/baseline/environment; explicit UTC `as_of`; explicit limitations |
| Claims | 1–32; nonempty statement, code references, and 1–16 scenarios each |
| Scenarios | At most 128 total; stable unique ID, description, mode, expected observation, blocking and semantic flags |
| Modes | Every claim needs positive, negative, and regression coverage; absent modes produce unknowns |
| Evidence | At most 256; 16,000-character content cap; content SHA-256; baseline/environment/time binding |
| Witness content | Exact JSON fields: scenario_id, actual, case_id, run_id, producer, method |
| Couplings | At most 64; declared source/target claims and witness scenario owned by the target |
| Input | At most 1 MiB of canonical request JSON; explicit CLI rejects duplicate JSON keys |
| IDs | Globally unique letters/digits/underscore/hyphen; 64 characters maximum |
| Timestamps | Explicit UTC; future and expired witnesses are unusable; host wall clock is never consulted |
| Admission | Always false; STABLE_AS_IS is scoped preservation, not certification |

Observations use exact string equality against the scenario expectation, defined outside the witness. Producers should normalize domain measurements in an independently governed collector. Numeric tolerances, statistical tests, fuzzing, attack generation, and semantic inference are not implemented here. Do not encode an LLM's unverified opinion as an executed result.

An evidence body is literal UTF-8 text. Its hash covers those exact bytes. The evaluator's contract hash covers canonical ASCII JSON with sorted object keys and ordered arrays. Replaying identical input with the same evaluator version returns identical output; reordering arrays changes the contract hash. Hashes are content identifiers, not signatures or evidence authenticity.

Unusable evidence remains in the report. Hash mismatches cause HOLD. Context mismatch, stale/future time, malformed witness content, scenario mismatch, and narrative-only content cause INSUFFICIENT_EVIDENCE. Two differing applicable observations for one scenario cause HOLD even when one matches. A failed blocking scenario takes HOLD precedence; otherwise a semantic failure causes SEMANTIC_DRIFT_DETECTED, and another failed scenario causes UPDATE_REQUIRED. A missing invariant witness remains unknown, not a witnessed invariant failure.

Finding/requirement IDs derive from tool ID, scenario (or claim for an undeclared mode), and reason code. They stay stable when a baseline version or evidence timestamp changes but the same gap remains. Requirement thresholds state the expected observation and collection condition. Baseline references point to the full input digest and available evidence. Regression obligations include every declared regression and blocking scenario; if none exist, the missing regression-mode finding must be resolved before a stable result is possible.

No candidate is applied or promoted. Requirements propose either collection, reconciliation, or bounded remediation. Improvement claims require external matched baseline/candidate campaigns, fixed environments, measurable thresholds, and unchanged-invariant witnesses. Those are method obligations; v1 does not compute causal effects or compare multiple baselines automatically.

`evaluate_coverage` and `derive_requirements` return typed assessment records. `emit_delta_report` also adds the full declared graph and two rendered views. Markdown embeds the structured result as JSON; Mermaid is the decision overview. HTML's graph retains every declared node/edge, with searchable views and no remote assets. Coupling paths expose declared links; they do not prove physical or runtime causality.
