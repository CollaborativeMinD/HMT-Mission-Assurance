"""Markdown and offline HTML views of the same structured evaluation."""

import base64
import hashlib
import html
from importlib.resources import files

from .contract import EvaluationContract
from .encoding import embedded_json
from .engine import derive_requirements
from .graph import build_graph
from .results import EvaluationResult, ReportBundle


def cell(value: object) -> str:
    text = html.escape(str(value), quote=True).replace("\n", " ").replace("\r", " ")
    for char in ("\\", "`", "*", "_", "[", "]", "|"):
        text = text.replace(char, "\\" + char)
    return text


def table(headers: tuple[str, ...], rows: list[tuple[object, ...]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(cell(v) for v in row) + " |" for row in rows)
    return "\n".join(lines) + "\n"


def trace_rows(contract: EvaluationContract, result: EvaluationResult) -> list[tuple[object, ...]]:
    rows: list[tuple[object, ...]] = []
    for claim in sorted(contract.claims, key=lambda c: c.id):
        for scenario in sorted(claim.scenarios, key=lambda s: s.id):
            evidence = [e.id for e in contract.evidence if e.scenario_id == scenario.id]
            findings = [f.id for f in result.findings if f.scenario_id == scenario.id]
            requirements = [r.id for r in result.requirements if r.finding_id in findings]
            rows.append(
                (
                    claim.id,
                    scenario.id,
                    scenario.mode,
                    scenario.expected,
                    ", ".join(evidence) or "MISSING",
                    ", ".join(findings) or "scoped match",
                    ", ".join(requirements) or "none",
                )
            )
    return rows


def findings_sections(contract: EvaluationContract, result: EvaluationResult) -> list[str]:
    return [
        "## Baseline claims\n",
        table(
            ("Claim", "Statement", "Implementation references"),
            [(c.id, c.statement, ", ".join(c.code_refs)) for c in contract.claims],
        ),
        "## Findings and hypotheses\n",
        table(
            ("Finding", "Disposition", "Expected", "Observed", "Evidence", "Hypothesis", "Release condition"),
            [
                (
                    f.id,
                    f.disposition,
                    f.expected,
                    f.observed,
                    ", ".join(f.evidence_refs) or "MISSING",
                    f.hypothesis,
                    f.release_condition,
                )
                for f in result.findings
            ],
        ),
        "## Falsifiable requirements and proposed changes\n",
        table(
            (
                "Requirement",
                "Gap",
                "Kind",
                "Baseline evidence",
                "Acceptance threshold",
                "Regression witness",
                "Proposed change",
            ),
            [
                (
                    r.id,
                    r.finding_id,
                    r.kind,
                    ", ".join(r.baseline_evidence_refs) or r.baseline_contract_ref,
                    r.acceptance_threshold,
                    ", ".join(r.regression_witness) or "Declare regression scenarios first",
                    r.proposed_change,
                )
                for r in result.requirements
            ],
        ),
        "If improvement is not demonstrated: preserve the baseline and do not promote.\n",
    ]


def trace_sections(contract: EvaluationContract, result: EvaluationResult) -> list[str]:
    return [
        "## Traceability matrix\n",
        table(
            ("Claim", "Scenario", "Mode", "Acceptance", "Evidence", "Findings", "Requirements"),
            trace_rows(contract, result),
        ),
        "## Declared couplings\n",
        table(
            ("Coupling", "Source", "Target", "Witness scenario", "Meaning"),
            [
                (c.id, c.source_claim, c.target_claim, c.scenario_id, c.description)
                for c in contract.couplings
            ],
        ),
        "## Evidence accountability\n",
        table(
            ("Evidence", "Source", "Producer context", "Captured UTC", "SHA-256", "Check"),
            [
                (
                    e.id,
                    e.source_ref,
                    f"{e.tool_id}/{e.baseline_version}/{e.environment_id}",
                    e.captured_at,
                    e.sha256,
                    next(c.reason_code for c in result.evidence_checks if c.evidence_id == e.id),
                )
                for e in contract.evidence
            ],
        ),
    ]


def markdown_report(contract: EvaluationContract, result: EvaluationResult) -> str:
    coverage = result.coverage
    sections = [
        "# Mission Assurance Delta Report\n",
        f"**{result.primary_disposition}** — {result.reason_code}\n",
        "Evaluation findings only. No security certification or implementation promotion is authorized.\n",
        table(
            ("Baseline", "Version", "Environment", "As of UTC", "Contract SHA-256"),
            [
                (
                    contract.tool_id,
                    contract.baseline_version,
                    contract.environment_id,
                    contract.as_of,
                    result.contract_sha256,
                )
            ],
        ),
        "## Scope and evidence basis\n",
        cell(contract.scope) + "\n",
        cell(result.evidence_basis) + "\n",
        "\n".join("- " + cell(item) for item in result.limitations) + "\n",
        table(
            ("Declared scenarios", "Exercised", "Satisfied", "Undeclared mode obligations"),
            [
                (
                    coverage.declared_scenarios,
                    coverage.exercised_scenarios,
                    coverage.satisfied_scenarios,
                    coverage.missing_mode_obligations,
                )
            ],
        ),
        "Counts cover the declared scenario set. They are not whole-project coverage or confidence scores.\n",
        *findings_sections(contract, result),
        *trace_sections(contract, result),
        "## Decision flow\n",
        '```mermaid\nflowchart TD\n  B["Declared baseline"] --> W["Submitted witnesses"]\n'
        '  W --> G["Gaps and contradictions"]\n  W --> D["' + result.primary_disposition + '"]\n'
        '  G --> R["Falsifiable requirements"]\n  G --> D\n```\n',
        "The complete graph, including every declared coupling, is in the structured record and offline HTML.\n",
        "## Machine-readable evaluation and graph\n",
        "```json\n" + embedded_json(result.model_dump(mode="json")) + "\n```\n",
    ]
    return "\n".join(sections)


def html_report(contract: EvaluationContract, result: EvaluationResult) -> str:
    template = files("hmt_mission_assurance").joinpath("data/report.html").read_text(encoding="utf-8")
    script = files("hmt_mission_assurance").joinpath("data/report.js").read_text(encoding="utf-8")
    digest = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    payload = embedded_json(
        {"contract": contract.model_dump(mode="json"), "evaluation": result.model_dump(mode="json")}
    )
    return (
        template.replace("__SCRIPT_HASH__", digest).replace("__SCRIPT__", script).replace("__DATA__", payload)
    )


def emit_delta_report(contract: EvaluationContract) -> ReportBundle:
    """Return report content; the caller decides whether and where to save it."""
    result = derive_requirements(contract)
    result = result.model_copy(update={"graph": build_graph(contract, result)})
    return ReportBundle(
        evaluation=result, markdown=markdown_report(contract, result), html=html_report(contract, result)
    )
