# Mission Assurance Delta Report

**UPDATE_REQUIRED** — OBSERVATION_CONTRADICTS_CONTRACT

Evaluation findings only. No security certification or implementation promotion is authorized.

| Baseline | Version | Environment | As of UTC | Contract SHA-256 |
| --- | --- | --- | --- | --- |
| example-gateway | demo-v1 | synthetic-demo | 2026-10-18T20:00:00Z | 21d58148b3a41969c350dd3d465a00128252a4fe017a6256baec52b83d616729 |

## Scope and evidence basis

Synthetic example: token acceptance/rejection and preservation of valid behavior.

Consistency of caller-supplied execution records against a caller-declared contract. Hashes verify content integrity, not producer identity, execution authenticity, or truth.

- Illustrative synthetic records; no gateway was executed.
- No general security claim.
- No independent execution or producer authentication is performed.
- No inference of completeness outside declared claims, scenarios, and couplings.
- A matching witness establishes neither causal attribution nor generalization.

| Declared scenarios | Exercised | Satisfied | Undeclared mode obligations |
| --- | --- | --- | --- |
| 3 | 3 | 2 | 0 |

Counts cover the declared scenario set. They are not whole-project coverage or confidence scores.

## Baseline claims

| Claim | Statement | Implementation references |
| --- | --- | --- |
| C-TOKEN | Valid tokens pass; invalid tokens are denied in these cases. | illustrative/gateway.py:authorize |

## Findings and hypotheses

| Finding | Disposition | Expected | Observed | Evidence | Hypothesis | Release condition |
| --- | --- | --- | --- | --- | --- | --- |
| F-d336a115e3effc1e1ed4 | UPDATE\_REQUIRED | denied | allowed | EV-1 | Unconfirmed: the implementation or evidence collection may omit this obligation. | Supply current, consistent execution witnesses satisfying: denied |

## Falsifiable requirements and proposed changes

| Requirement | Gap | Kind | Baseline evidence | Acceptance threshold | Regression witness | Proposed change |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-d336a115e3effc1e1ed4 | F-d336a115e3effc1e1ed4 | remediate | EV-1 | Supply current, consistent execution witnesses satisfying: denied | S-REGRESS | Propose a bounded correction, reproduce the discrepancy, and rerun affected obligations. |

If improvement is not demonstrated: preserve the baseline and do not promote.

## Traceability matrix

| Claim | Scenario | Mode | Acceptance | Evidence | Findings | Requirements |
| --- | --- | --- | --- | --- | --- | --- |
| C-TOKEN | S-INVALID | negative | denied | EV-1 | F-d336a115e3effc1e1ed4 | REQ-d336a115e3effc1e1ed4 |
| C-TOKEN | S-REGRESS | regression | allowed | EV-2 | scoped match | none |
| C-TOKEN | S-VALID | positive | allowed | EV-0 | scoped match | none |

## Declared couplings

| Coupling | Source | Target | Witness scenario | Meaning |
| --- | --- | --- | --- | --- |

## Evidence accountability

| Evidence | Source | Producer context | Captured UTC | SHA-256 | Check |
| --- | --- | --- | --- | --- | --- |
| EV-0 | synthetic-demo:S-VALID | example-gateway/demo-v1/synthetic-demo | 2026-10-18T19:59:00Z | 90a33e16e07affce7f49de90c2bf41cd31f553ac9462450c8f4dd56310db4133 | USABLE\_SUBMITTED\_WITNESS |
| EV-1 | synthetic-demo:S-INVALID | example-gateway/demo-v1/synthetic-demo | 2026-10-18T19:59:00Z | bc4a8c008b1793d479c280d137b28cb2810987e3ed661b9a0354b41f9c6e7c34 | USABLE\_SUBMITTED\_WITNESS |
| EV-2 | synthetic-demo:S-REGRESS | example-gateway/demo-v1/synthetic-demo | 2026-10-18T19:59:00Z | 111ec6d54ecd57644741e65edd2ffe9be14e2e47007718298ba35930693cf864 | USABLE\_SUBMITTED\_WITNESS |

## Decision flow

```mermaid
flowchart TD
  B["Declared baseline"] --> W["Submitted witnesses"]
  W --> G["Gaps and contradictions"]
  W --> D["UPDATE_REQUIRED"]
  G --> R["Falsifiable requirements"]
  G --> D
```

The complete graph, including every declared coupling, is in the structured record and offline HTML.

## Machine-readable evaluation and graph

```json
{"admission_authorized":false,"as_of":"2026-10-18T20:00:00Z","baseline_version":"demo-v1","contract_sha256":"21d58148b3a41969c350dd3d465a00128252a4fe017a6256baec52b83d616729","coverage":{"basis":"declared_scenarios_only","declared_scenarios":3,"exercised_scenarios":3,"missing_mode_obligations":0,"satisfied_scenarios":2},"delta_required":true,"evaluator_version":"0.1.0","evidence_basis":"Consistency of caller-supplied execution records against a caller-declared contract. Hashes verify content integrity, not producer identity, execution authenticity, or truth.","evidence_checks":[{"actual":"allowed","evidence_id":"EV-0","reason_code":"USABLE_SUBMITTED_WITNESS","scenario_id":"S-VALID","usable":true},{"actual":"allowed","evidence_id":"EV-1","reason_code":"USABLE_SUBMITTED_WITNESS","scenario_id":"S-INVALID","usable":true},{"actual":"allowed","evidence_id":"EV-2","reason_code":"USABLE_SUBMITTED_WITNESS","scenario_id":"S-REGRESS","usable":true}],"findings":[{"claim_id":"C-TOKEN","disposition":"UPDATE_REQUIRED","evidence_refs":["EV-1"],"expected":"denied","hypothesis":"Unconfirmed: the implementation or evidence collection may omit this obligation.","id":"F-d336a115e3effc1e1ed4","observed":"allowed","reason_code":"OBSERVATION_CONTRADICTS_CONTRACT","release_condition":"Supply current, consistent execution witnesses satisfying: denied","scenario_id":"S-INVALID"}],"graph":{"edges":[{"relation":"negative","source":"claim:C-TOKEN","target":"scenario:S-INVALID"},{"relation":"regression","source":"claim:C-TOKEN","target":"scenario:S-REGRESS"},{"relation":"positive","source":"claim:C-TOKEN","target":"scenario:S-VALID"},{"relation":"basis","source":"evidence:EV-1","target":"finding:F-d336a115e3effc1e1ed4"},{"relation":"UPDATE_REQUIRED","source":"finding:F-d336a115e3effc1e1ed4","target":"disposition:primary"},{"relation":"derive","source":"finding:F-d336a115e3effc1e1ed4","target":"requirement:REQ-d336a115e3effc1e1ed4"},{"relation":"submitted","source":"scenario:S-INVALID","target":"evidence:EV-1"},{"relation":"finding","source":"scenario:S-INVALID","target":"finding:F-d336a115e3effc1e1ed4"},{"relation":"submitted","source":"scenario:S-REGRESS","target":"evidence:EV-2"},{"relation":"submitted","source":"scenario:S-VALID","target":"evidence:EV-0"}],"nodes":[{"id":"claim:C-TOKEN","kind":"claim","label":"Valid tokens pass; invalid tokens are denied in these cases."},{"id":"disposition:primary","kind":"disposition","label":"UPDATE_REQUIRED"},{"id":"evidence:EV-0","kind":"evidence","label":"synthetic-demo:S-VALID"},{"id":"evidence:EV-1","kind":"evidence","label":"synthetic-demo:S-INVALID"},{"id":"evidence:EV-2","kind":"evidence","label":"synthetic-demo:S-REGRESS"},{"id":"finding:F-d336a115e3effc1e1ed4","kind":"finding","label":"OBSERVATION_CONTRADICTS_CONTRACT"},{"id":"requirement:REQ-d336a115e3effc1e1ed4","kind":"requirement","label":"Supply current, consistent execution witnesses satisfying: denied"},{"id":"scenario:S-INVALID","kind":"scenario","label":"Invalid token"},{"id":"scenario:S-REGRESS","kind":"scenario","label":"Previously valid token still passes"},{"id":"scenario:S-VALID","kind":"scenario","label":"Valid token"}]},"limitations":["Illustrative synthetic records; no gateway was executed.","No general security claim.","No independent execution or producer authentication is performed.","No inference of completeness outside declared claims, scenarios, and couplings.","A matching witness establishes neither causal attribution nor generalization."],"primary_disposition":"UPDATE_REQUIRED","reason_code":"OBSERVATION_CONTRADICTS_CONTRACT","requirements":[{"acceptance_threshold":"Supply current, consistent execution witnesses satisfying: denied","baseline_contract_ref":"21d58148b3a41969c350dd3d465a00128252a4fe017a6256baec52b83d616729","baseline_evidence_refs":["EV-1"],"finding_id":"F-d336a115e3effc1e1ed4","id":"REQ-d336a115e3effc1e1ed4","if_not_demonstrated":"preserve_baseline_and_do_not_promote","kind":"remediate","proposed_change":"Propose a bounded correction, reproduce the discrepancy, and rerun affected obligations.","regression_witness":["S-REGRESS"]}],"scope":"Synthetic example: token acceptance/rejection and preservation of valid behavior.","security_certification":false,"tool_id":"example-gateway"}
```
