"""Check integrity, applicability, and submitted observations without executing them."""

from .contract import EvaluationContract, Evidence, Witness, utc_time
from .encoding import canonical, parse_json, sha256
from .results import BaselineInspection, EvidenceCheck

BASIS = (
    "Consistency of caller-supplied execution records against a caller-declared contract. "
    "Hashes verify content integrity, not producer identity, execution authenticity, or truth."
)


def check_evidence(contract: EvaluationContract, evidence: Evidence) -> EvidenceCheck:
    reason, actual = "USABLE_SUBMITTED_WITNESS", None
    if sha256(evidence.content) != evidence.sha256:
        reason = "EVIDENCE_HASH_MISMATCH"
    elif (evidence.tool_id, evidence.baseline_version, evidence.environment_id) != (
        contract.tool_id,
        contract.baseline_version,
        contract.environment_id,
    ):
        reason = "EVIDENCE_CONTEXT_MISMATCH"
    else:
        age = (utc_time(contract.as_of) - utc_time(evidence.captured_at)).total_seconds()
        if age < 0 or age > contract.max_age_seconds:
            reason = "EVIDENCE_OUTSIDE_TIME_WINDOW"
        else:
            reason, actual = parse_witness(evidence)
    return EvidenceCheck(
        evidence_id=evidence.id,
        scenario_id=evidence.scenario_id,
        usable=reason == "USABLE_SUBMITTED_WITNESS",
        reason_code=reason,
        actual=actual,
    )


def parse_witness(evidence: Evidence) -> tuple[str, str | None]:
    try:
        raw = parse_json(evidence.content)
        witness = Witness.model_validate_json(canonical(raw))
    except (ValueError, RecursionError):
        return "MALFORMED_WITNESS", None
    if witness.scenario_id != evidence.scenario_id:
        return "WITNESS_SCENARIO_MISMATCH", None
    if witness.method != "executed":
        return "NARRATIVE_IS_NOT_EXECUTION", None
    return "USABLE_SUBMITTED_WITNESS", witness.actual


def inspect_baseline(contract: EvaluationContract) -> BaselineInspection:
    """Establish which declared scenarios have matching submitted execution records."""
    checks = tuple(check_evidence(contract, e) for e in sorted(contract.evidence, key=lambda e: e.id))
    demonstrated = []
    for claim in sorted(contract.claims, key=lambda c: c.id):
        for scenario in sorted(claim.scenarios, key=lambda s: s.id):
            actuals = {c.actual for c in checks if c.usable and c.scenario_id == scenario.id}
            if actuals == {scenario.expected}:
                demonstrated.append(scenario.id)
    return BaselineInspection(
        contract_sha256=sha256(canonical(contract.model_dump(mode="json"))),
        tool_id=contract.tool_id,
        baseline_version=contract.baseline_version,
        declared_claims=tuple(c.statement for c in sorted(contract.claims, key=lambda c: c.id)),
        demonstrated_scenarios=tuple(demonstrated),
        evidence_checks=checks,
        evidence_basis=BASIS,
    )
