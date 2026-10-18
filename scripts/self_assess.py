"""Evaluate this implementation using actual local validation receipts."""

import json
import platform
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

from hmt_mission_assurance.contract import EvaluationContract
from hmt_mission_assurance.encoding import canonical, sha256
from hmt_mission_assurance.reports import emit_delta_report

ROOT = Path(__file__).resolve().parents[1]
GROUPS = {
    "CONTRACT": (
        "Typed input and evidence checks in selected cases",
        "contract.py",
        ["test_scoped_stability", "test_dangling_evidence", "test_requirement_identity_and_evidence_binding"],
    ),
    "READONLY": (
        "Read-only MCP and repeatable evaluation in selected cases",
        "server.py",
        [
            "test_stdio_protocol",
            "test_source_reference_never_fetches",
            "test_replay_and_cross_call_isolation",
        ],
    ),
    "REPORT": (
        "Faithful graph and inert untrusted text in selected cases",
        "reports.py",
        [
            "test_graph_fidelity_and_machine_record",
            "test_html_and_markdown_injection",
            "test_full_findings_and_requirements_visible",
        ],
    ),
}


def source_digest() -> str:
    paths = list((ROOT / "src").rglob("*.py")) + list((ROOT / "src").rglob("*.js"))
    paths += list((ROOT / "src").rglob("*.html")) + [
        ROOT / "SKILL.md",
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
    ]
    paths += list((ROOT / "tests").glob("*.py")) + list((ROOT / "scripts").glob("*.py"))
    return sha256(canonical({str(p.relative_to(ROOT)): sha256(p.read_text()) for p in sorted(paths)}))


def self_contract(timestamp: str) -> EvaluationContract:
    root = ET.parse(ROOT / "evidence/junit.xml").getroot()
    cases = {c.attrib["name"]: c for c in root.iter("testcase")}
    raw = {
        "tool_id": "hmt-mission-assurance",
        "baseline_version": "0.1.0+source." + source_digest()[:16],
        "scope": "Consistency of selected actual local pytest execution records and implementation obligations.",
        "limitations": [
            "Local Python " + platform.python_version() + "; hosted CI is a separate witness.",
            "Producer assertions are locally generated and not independently authenticated.",
            "No whole-project security, causal improvement, or generalization claim.",
        ],
        "as_of": timestamp,
        "environment_id": "local-python-" + platform.python_version().replace(".", "-"),
        "max_age_seconds": 86400,
        "claims": [],
        "evidence": [],
        "couplings": [],
    }
    for group, info in GROUPS.items():
        add_group(raw, cases, group, info, timestamp)
    raw["couplings"] = [
        {
            "id": "K-REPORT-INPUT",
            "source_claim": "C-CONTRACT",
            "target_claim": "C-REPORT",
            "scenario_id": "S-REPORT-negative",
            "description": "Untrusted contract strings remain inert in rendered reports.",
        }
    ]
    return EvaluationContract.model_validate_json(canonical(raw))


def add_group(raw: dict, cases: dict, group: str, info: tuple, timestamp: str) -> None:
    statement, path, tests = info
    scenarios = []
    for mode, test in zip(("positive", "negative", "regression"), tests, strict=True):
        case = cases[test]
        actual = "passed" if not list(case) else "not-passed"
        sid = f"S-{group}-{mode}"
        scenarios.append({"id": sid, "description": test, "mode": mode, "expected": "passed"})
        content = canonical(
            {
                "scenario_id": sid,
                "actual": actual,
                "case_id": test,
                "run_id": "RUN-LOCAL-VALIDATION",
                "producer": "pytest-junit-receipt",
                "method": "executed",
            }
        )
        raw["evidence"].append(
            {
                "id": "EV-" + sid,
                "scenario_id": sid,
                "source_ref": "evidence/junit.xml:" + test,
                "tool_id": raw["tool_id"],
                "baseline_version": raw["baseline_version"],
                "environment_id": raw["environment_id"],
                "captured_at": datetime.fromtimestamp(
                    (ROOT / "evidence/junit.xml").stat().st_mtime, UTC
                ).isoformat(),
                "content": content,
                "sha256": sha256(content),
            }
        )
    raw["claims"].append(
        {
            "id": "C-" + group,
            "statement": statement,
            "code_refs": ["src/hmt_mission_assurance/" + path],
            "scenarios": scenarios,
        }
    )


def main() -> None:
    timestamp = datetime.now(UTC).isoformat()
    contract = self_contract(timestamp)
    bundle = emit_delta_report(contract)
    assert bundle.evaluation.primary_disposition == "STABLE_AS_IS"
    outputs = {
        "self-contract.json": json.dumps(contract.model_dump(mode="json"), indent=2),
        "self-assessment.json": json.dumps(bundle.evaluation.model_dump(mode="json"), indent=2),
        "self-assessment.md": bundle.markdown,
        "self-assessment.html": bundle.html,
    }
    for name, content in outputs.items():
        (ROOT / "evidence" / name).write_text(content + "\n")
    print("G-SELF-010: PASS (selected local witnesses; no certification or admission)")


if __name__ == "__main__":
    main()
