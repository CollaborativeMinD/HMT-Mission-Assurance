"""Regenerate public synthetic examples and the schema; --check writes nothing."""

import argparse
import json
from pathlib import Path

from hmt_mission_assurance.contract import EvaluationContract
from hmt_mission_assurance.encoding import canonical, sha256
from hmt_mission_assurance.reports import emit_delta_report

ROOT = Path(__file__).resolve().parents[1]


def example() -> dict:
    return {
        "schema_version": "1.0",
        "tool_id": "example-gateway",
        "baseline_version": "demo-v1",
        "scope": "Synthetic example: token acceptance/rejection and preservation of valid behavior.",
        "limitations": [
            "Illustrative synthetic records; no gateway was executed.",
            "No general security claim.",
        ],
        "as_of": "2026-10-18T20:00:00Z",
        "environment_id": "synthetic-demo",
        "max_age_seconds": 3600,
        "claims": [
            {
                "id": "C-TOKEN",
                "statement": "Valid tokens pass; invalid tokens are denied in these cases.",
                "code_refs": ["illustrative/gateway.py:authorize"],
                "scenarios": [
                    {
                        "id": "S-VALID",
                        "description": "Valid token",
                        "mode": "positive",
                        "expected": "allowed",
                    },
                    {
                        "id": "S-INVALID",
                        "description": "Invalid token",
                        "mode": "negative",
                        "expected": "denied",
                    },
                    {
                        "id": "S-REGRESS",
                        "description": "Previously valid token still passes",
                        "mode": "regression",
                        "expected": "allowed",
                    },
                ],
            }
        ],
        "evidence": [],
        "couplings": [],
    }


def witness(contract: dict, scenario: str, actual: str, index: int) -> dict:
    content = canonical(
        {
            "scenario_id": scenario,
            "actual": actual,
            "case_id": f"demo/{scenario}",
            "run_id": "SYNTHETIC-RUN",
            "producer": "synthetic-example-builder",
            "method": "executed",
        }
    )
    return {
        "id": f"EV-{index}",
        "scenario_id": scenario,
        "source_ref": f"synthetic-demo:{scenario}",
        "tool_id": contract["tool_id"],
        "baseline_version": contract["baseline_version"],
        "environment_id": contract["environment_id"],
        "captured_at": "2026-10-18T19:59:00Z",
        "content": content,
        "sha256": sha256(content),
    }


def generated() -> dict[Path, str]:
    outputs = {}
    for stage in ("before", "gap", "after", "coupled"):
        raw = example()
        if stage in ("after", "coupled"):
            raw["baseline_version"] = "demo-v2"
        for index, scenario in enumerate(raw["claims"][0]["scenarios"]):
            if stage == "before" and index:
                continue
            actual = "allowed" if stage == "gap" and index == 1 else scenario["expected"]
            raw["evidence"].append(witness(raw, scenario["id"], actual, index))
        if stage == "coupled":
            second = json.loads(json.dumps(raw["claims"][0]))
            second.update(
                id="C-AUDIT", statement="Authorization outcomes retain audit records in these cases."
            )
            for index, scenario in enumerate(second["scenarios"]):
                scenario["id"] = "A-" + scenario["id"]
                scenario["expected"] = "recorded"
                raw["evidence"].append(witness(raw, scenario["id"], "recorded", index + 3))
            raw["claims"].append(second)
            raw["couplings"] = [
                {
                    "id": "K-AUDIT",
                    "source_claim": "C-TOKEN",
                    "target_claim": "C-AUDIT",
                    "scenario_id": "A-S-INVALID",
                    "description": "Denied token outcomes reach the audit seam.",
                }
            ]
        contract = EvaluationContract.model_validate_json(canonical(raw))
        bundle = emit_delta_report(contract)
        outputs[ROOT / "examples" / f"{stage}.json"] = json.dumps(raw, indent=2) + "\n"
        for extension, content in (
            ("md", bundle.markdown),
            ("html", bundle.html),
            ("json", json.dumps(bundle.evaluation.model_dump(mode="json"), indent=2) + "\n"),
        ):
            outputs[ROOT / "examples" / stage / f"delta-report.{extension}"] = content
    outputs[ROOT / "src/hmt_mission_assurance/data/example.json"] = outputs[ROOT / "examples/before.json"]
    outputs[ROOT / "schemas/evaluation-contract.schema.json"] = (
        json.dumps(EvaluationContract.model_json_schema(), indent=2) + "\n"
    )
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for path, content in generated().items():
        if args.check:
            assert path.read_text() == content, f"Generated artifact is stale: {path.relative_to(ROOT)}"
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    print("Examples and schema: PASS")


if __name__ == "__main__":
    main()
