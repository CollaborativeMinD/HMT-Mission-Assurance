import copy

import pytest
from pydantic import ValidationError

from hmt_mission_assurance.contract import EvaluationContract, utc_time
from hmt_mission_assurance.encoding import MAX_INPUT_BYTES, canonical, parse_json


@pytest.mark.parametrize(
    "change",
    [
        {"unexpected": "ignore me"},
        {"max_age_seconds": "3600"},
        {"max_age_seconds": True},
        {"max_age_seconds": 0},
        {"scope": "   "},
        {"tool_id": "x```\nattack"},
        {"as_of": "2026-10-18T20:00:00"},
        {"as_of": "2026-10-18T20:00:00+02:00"},
        {"as_of": "no"},
        {"claims": []},
        {"schema_version": "2.0"},
    ],
)
def test_strict_contract(raw, change):
    raw.update(change)
    with pytest.raises(ValidationError):
        EvaluationContract.model_validate_json(canonical(raw))


@pytest.mark.parametrize("target", ["claim", "scenario", "evidence", "nested"])
def test_duplicate_and_nested_fields(raw, target):
    if target == "claim":
        raw["claims"].append(copy.deepcopy(raw["claims"][0]))
    elif target == "scenario":
        raw["claims"][0]["scenarios"][1]["id"] = raw["claims"][0]["scenarios"][0]["id"]
    elif target == "evidence":
        raw["evidence"][0]["id"] = raw["claims"][0]["id"]
    else:
        raw["claims"][0]["scenarios"][0]["command"] = "execute something"
    with pytest.raises(ValidationError):
        EvaluationContract.model_validate_json(canonical(raw))


def test_dangling_evidence(raw):
    raw["evidence"][0]["scenario_id"] = "UNKNOWN"
    with pytest.raises(ValidationError):
        EvaluationContract.model_validate_json(canonical(raw))


@pytest.mark.parametrize("kind", ["claim", "scenario", "self"])
def test_invalid_coupling(raw, kind):
    raw["couplings"] = [
        {
            "id": "K",
            "source_claim": "C-TOKEN",
            "target_claim": "UNKNOWN",
            "scenario_id": "S-INVALID",
            "description": "seam",
        }
    ]
    if kind == "scenario":
        second = copy.deepcopy(raw["claims"][0])
        second["id"] = "C-OTHER"
        for s in second["scenarios"]:
            s["id"] = "OTHER-" + s["id"]
        raw["claims"].append(second)
        raw["couplings"][0]["target_claim"] = "C-OTHER"
    if kind == "self":
        raw["couplings"][0]["target_claim"] = "C-TOKEN"
    with pytest.raises(ValidationError):
        EvaluationContract.model_validate_json(canonical(raw))


def test_total_scenario_limit(raw):
    claim = raw["claims"][0]
    raw["claims"] = []
    for i in range(9):
        c = copy.deepcopy(claim)
        c["id"] = f"C-{i}"
        c["scenarios"] = [dict(claim["scenarios"][0], id=f"S-{i}-{j}") for j in range(16)]
        raw["claims"].append(c)
    raw["evidence"] = []
    with pytest.raises(ValidationError):
        EvaluationContract.model_validate_json(canonical(raw))


def test_duplicate_json_and_size():
    with pytest.raises(ValueError, match="duplicate"):
        parse_json('{"x":1,"x":2}')
    with pytest.raises(ValueError, match="1 MiB"):
        parse_json('"' + "x" * MAX_INPUT_BYTES + '"')
    with pytest.raises(ValueError):
        canonical({"x": float("nan")})
    assert utc_time("2026-10-18T20:00:00Z").hour == 20
