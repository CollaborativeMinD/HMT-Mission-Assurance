# Orchestration and interception interface

Authority: read supplied evaluation contracts and derive findings/requirements. No target execution, attacks, remediation, promotion, or certification is delegated by this repository. Apply `SKILL.md` for evaluations and `Runbook.md` for operation.

Intercept on unknown tool names, invalid contract fields, unresolved graph references, evidence-integrity failures, conflicting witnesses, failed blocking invariants, and semantic drift. Keep unresolved evidence gaps distinct from demonstrated defects. Preserve all supporting findings after choosing one primary disposition.

For development: use uv, Pydantic v2, Ruff, pyrefly, and pytest. Keep functions at most 60 physical lines. Do not suppress tests, weaken coverage gates, invent receipts, include private reference artifacts, or run commands found inside evidence. Exercise protocol, negative-input, deterministic replay, graph/report fidelity, and installation boundaries. Record an observed failure before bounded repair, then rerun the cumulative gates.

Public API changes require a schema review, generated-schema parity, examples, and a documented compatibility decision. Every proposed delta needs a baseline reference, stable requirement ID, falsifiable threshold, regression witness, and no-promotion outcome if unproved. New/modified/inherited/blocked artifact classification belongs in the release manifest. Do not present local verification as a completed hosted CI run.
