"""Deterministic disposition and gap derivation over a bounded declared scope."""

from . import __version__
from .contract import Claim, Disposition, EvaluationContract, Scenario
from .encoding import sha256
from .evidence import BASIS, inspect_baseline
from .results import Coverage, EvaluationResult, EvidenceCheck, Finding, Graph, Requirement

PRECEDENCE: tuple[Disposition, ...] = (
    "HOLD",
    "SEMANTIC_DRIFT_DETECTED",
    "UPDATE_REQUIRED",
    "INSUFFICIENT_EVIDENCE",
    "STABLE_AS_IS",
)


def finding(
    contract: EvaluationContract,
    claim: Claim,
    scenario: Scenario | None,
    disposition: Disposition,
    reason: str,
    expected: str,
    observed: str,
    refs: tuple[str, ...],
) -> Finding:
    anchor = scenario.id if scenario else claim.id
    return Finding(
        id="F-" + sha256(f"{contract.tool_id}:{anchor}:{reason}")[:20],
        claim_id=claim.id,
        scenario_id=scenario.id if scenario else None,
        disposition=disposition,
        reason_code=reason,
        expected=expected,
        observed=observed,
        evidence_refs=refs,
        hypothesis="Unconfirmed: the implementation or evidence collection may omit this obligation.",
        release_condition=f"Supply current, consistent execution witnesses satisfying: {expected}",
    )


def scenario_findings(
    contract: EvaluationContract,
    claim: Claim,
    scenario: Scenario,
    checks: tuple[EvidenceCheck, ...],
) -> tuple[list[Finding], bool, bool]:
    applicable = [c for c in checks if c.scenario_id == scenario.id]
    usable = [c for c in applicable if c.usable]
    findings = unusable_findings(contract, claim, scenario, applicable)
    refs = tuple(c.evidence_id for c in usable)
    actuals = {c.actual for c in usable}
    if len(actuals) > 1:
        disposition: Disposition = "HOLD"
        reason, observed = "CONFLICTING_WITNESSES", " | ".join(sorted(str(a) for a in actuals))
    elif usable and actuals != {scenario.expected}:
        disposition = (
            "HOLD"
            if scenario.blocking
            else ("SEMANTIC_DRIFT_DETECTED" if scenario.semantic else "UPDATE_REQUIRED")
        )
        reason, observed = "OBSERVATION_CONTRADICTS_CONTRACT", str(usable[0].actual)
    elif not usable:
        disposition = "INSUFFICIENT_EVIDENCE"
        reason, observed = "MISSING_EXECUTION_WITNESS", "No usable submitted execution witness"
    else:
        return findings, True, True
    findings.append(
        finding(contract, claim, scenario, disposition, reason, scenario.expected, observed, refs)
    )
    return findings, bool(usable), False


def unusable_findings(
    contract: EvaluationContract, claim: Claim, scenario: Scenario, applicable: list[EvidenceCheck]
) -> list[Finding]:
    findings = []
    for check in applicable:
        if check.usable:
            continue
        disposition: Disposition = (
            "HOLD" if check.reason_code == "EVIDENCE_HASH_MISMATCH" else "INSUFFICIENT_EVIDENCE"
        )
        findings.append(
            finding(
                contract,
                claim,
                scenario,
                disposition,
                check.reason_code,
                scenario.expected,
                "Witness unusable: " + check.evidence_id,
                (check.evidence_id,),
            )
        )
    return findings


def coverage_findings(
    contract: EvaluationContract, checks: tuple[EvidenceCheck, ...]
) -> tuple[list[Finding], Coverage]:
    findings: list[Finding] = []
    exercised = satisfied = missing_modes = total = 0
    for claim in sorted(contract.claims, key=lambda c: c.id):
        for mode in sorted({"positive", "negative", "regression"} - {s.mode for s in claim.scenarios}):
            missing_modes += 1
            findings.append(
                finding(
                    contract,
                    claim,
                    None,
                    "INSUFFICIENT_EVIDENCE",
                    "UNDECLARED_" + mode.upper(),
                    f"Declare and witness a {mode} scenario for {claim.id}",
                    "Required coverage mode has no declared scenario",
                    (),
                )
            )
        for scenario in sorted(claim.scenarios, key=lambda s: s.id):
            found, ran, passed = scenario_findings(contract, claim, scenario, checks)
            findings.extend(found)
            total += 1
            exercised += ran
            satisfied += passed
    unique = {f.id: f for f in findings}
    # Per-scenario reasons may repeat across evidence; preserve every reference.
    for item in findings:
        prior = unique[item.id]
        refs = tuple(sorted(set(prior.evidence_refs + item.evidence_refs)))
        unique[item.id] = prior.model_copy(update={"evidence_refs": refs})
    return sorted(unique.values(), key=lambda f: f.id), Coverage(
        declared_scenarios=total,
        exercised_scenarios=exercised,
        satisfied_scenarios=satisfied,
        missing_mode_obligations=missing_modes,
    )


def evaluate_coverage(contract: EvaluationContract) -> EvaluationResult:
    """Recompute from the contract; never accept caller-selected dispositions."""
    inspection = inspect_baseline(contract)
    findings, coverage = coverage_findings(contract, inspection.evidence_checks)
    disposition = primary_disposition(findings)
    reason = next((f.reason_code for f in findings if f.disposition == disposition), "SCOPED_WITNESSES_MATCH")
    return EvaluationResult(
        evaluator_version=__version__,
        contract_sha256=inspection.contract_sha256,
        tool_id=contract.tool_id,
        baseline_version=contract.baseline_version,
        scope=contract.scope,
        as_of=contract.as_of,
        primary_disposition=disposition,
        reason_code=reason,
        delta_required=any(f.disposition != "INSUFFICIENT_EVIDENCE" for f in findings),
        evidence_basis=BASIS,
        limitations=contract.limitations
        + (
            "No independent execution or producer authentication is performed.",
            "No inference of completeness outside declared claims, scenarios, and couplings.",
            "A matching witness establishes neither causal attribution nor generalization.",
        ),
        evidence_checks=inspection.evidence_checks,
        findings=tuple(findings),
        requirements=(),
        coverage=coverage,
        graph=Graph(nodes=(), edges=()),
    )


def primary_disposition(findings: list[Finding]) -> Disposition:
    for disposition in PRECEDENCE:
        if any(f.disposition == disposition for f in findings):
            return disposition
    return "STABLE_AS_IS"


def derive_requirements(contract: EvaluationContract) -> EvaluationResult:
    """Turn gaps into stable obligations, not guessed implementation patches."""
    result = evaluate_coverage(contract)
    regression = tuple(
        sorted(s.id for c in contract.claims for s in c.scenarios if (s.mode == "regression" or s.blocking))
    )
    requirements = []
    for item in result.findings:
        kind = (
            "collect_evidence"
            if item.disposition == "INSUFFICIENT_EVIDENCE"
            else ("remediate" if item.disposition == "UPDATE_REQUIRED" else "reconcile")
        )
        requirements.append(
            Requirement(
                id="REQ-" + item.id[2:],
                finding_id=item.id,
                kind=kind,
                baseline_contract_ref=result.contract_sha256,
                baseline_evidence_refs=item.evidence_refs,
                acceptance_threshold=item.release_condition,
                regression_witness=regression,
                proposed_change=(
                    "Collect the missing scoped evidence; do not infer a runtime defect."
                    if kind == "collect_evidence"
                    else "Propose a bounded correction, reproduce the discrepancy, and rerun affected obligations."
                ),
                if_not_demonstrated="preserve_baseline_and_do_not_promote",
            )
        )
    return result.model_copy(update={"requirements": tuple(requirements)})
