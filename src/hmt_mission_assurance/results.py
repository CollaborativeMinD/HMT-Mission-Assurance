"""Typed outputs share one deterministic lineage back to the input contract."""

from typing import Literal

from .contract import Disposition, Model


class EvidenceCheck(Model):
    evidence_id: str
    scenario_id: str
    usable: bool
    reason_code: str
    actual: str | None = None


class Finding(Model):
    id: str
    claim_id: str
    scenario_id: str | None
    disposition: Disposition
    reason_code: str
    expected: str
    observed: str
    evidence_refs: tuple[str, ...]
    hypothesis: str
    release_condition: str


class Requirement(Model):
    id: str
    finding_id: str
    kind: Literal["collect_evidence", "reconcile", "remediate"]
    baseline_contract_ref: str
    baseline_evidence_refs: tuple[str, ...]
    acceptance_threshold: str
    regression_witness: tuple[str, ...]
    proposed_change: str
    if_not_demonstrated: Literal["preserve_baseline_and_do_not_promote"]


class Coverage(Model):
    declared_scenarios: int
    exercised_scenarios: int
    satisfied_scenarios: int
    missing_mode_obligations: int
    basis: Literal["declared_scenarios_only"] = "declared_scenarios_only"


class Node(Model):
    id: str
    kind: str
    label: str


class Edge(Model):
    source: str
    target: str
    relation: str


class Graph(Model):
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]


class EvaluationResult(Model):
    evaluator_version: str
    contract_sha256: str
    tool_id: str
    baseline_version: str
    scope: str
    as_of: str
    primary_disposition: Disposition
    reason_code: str
    delta_required: bool
    admission_authorized: Literal[False] = False
    security_certification: Literal[False] = False
    evidence_basis: str
    limitations: tuple[str, ...]
    evidence_checks: tuple[EvidenceCheck, ...]
    findings: tuple[Finding, ...]
    requirements: tuple[Requirement, ...]
    coverage: Coverage
    graph: Graph


class BaselineInspection(Model):
    contract_sha256: str
    tool_id: str
    baseline_version: str
    declared_claims: tuple[str, ...]
    demonstrated_scenarios: tuple[str, ...]
    evidence_checks: tuple[EvidenceCheck, ...]
    evidence_basis: str


class ReportBundle(Model):
    evaluation: EvaluationResult
    markdown: str
    html: str
