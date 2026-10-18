import copy
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from hmt_mission_assurance.contract import EvaluationContract
from hmt_mission_assurance.encoding import canonical, sha256
from hmt_mission_assurance.engine import derive_requirements, evaluate_coverage
from hmt_mission_assurance.evidence import inspect_baseline


def load(raw):
    return EvaluationContract.model_validate_json(canonical(raw))


def rewrite(record, **change):
    value = json.loads(record["content"])
    value.update(change)
    record["content"] = canonical(value)
    record["sha256"] = sha256(record["content"])


def test_scoped_stability(contract):
    result = evaluate_coverage(contract)
    assert result.primary_disposition == "STABLE_AS_IS"
    assert not result.findings and not result.admission_authorized and not result.security_certification
    assert result.coverage.satisfied_scenarios == 3
    assert len(inspect_baseline(contract).demonstrated_scenarios) == 3


def test_missing_is_unknown(raw):
    raw["evidence"] = raw["evidence"][:1]
    result = derive_requirements(load(raw))
    assert result.primary_disposition == "INSUFFICIENT_EVIDENCE"
    assert len(result.findings) == 2
    assert all(r.kind == "collect_evidence" for r in result.requirements)
    assert all(r.baseline_contract_ref == result.contract_sha256 for r in result.requirements)
    assert not result.delta_required


@pytest.mark.parametrize(
    ("flags", "disposition"),
    [
        ({}, "UPDATE_REQUIRED"),
        ({"semantic": True}, "SEMANTIC_DRIFT_DETECTED"),
        ({"blocking": True}, "HOLD"),
        ({"semantic": True, "blocking": True}, "HOLD"),
    ],
)
def test_witnessed_failure(raw, flags, disposition):
    raw["claims"][0]["scenarios"][1].update(flags)
    rewrite(raw["evidence"][1], actual="allowed")
    result = derive_requirements(load(raw))
    assert result.primary_disposition == disposition
    assert result.delta_required
    assert result.findings[0].evidence_refs == ("EV-1",)
    assert result.requirements[0].regression_witness
    assert not result.admission_authorized


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"baseline_version": "old"}, "EVIDENCE_CONTEXT_MISMATCH"),
        ({"tool_id": "other"}, "EVIDENCE_CONTEXT_MISMATCH"),
        ({"environment_id": "other"}, "EVIDENCE_CONTEXT_MISMATCH"),
        ({"captured_at": "2026-10-17T00:00:00Z"}, "EVIDENCE_OUTSIDE_TIME_WINDOW"),
        ({"captured_at": "2026-10-19T00:00:00Z"}, "EVIDENCE_OUTSIDE_TIME_WINDOW"),
    ],
)
def test_unusable_evidence(raw, change, reason):
    raw["evidence"][1].update(change)
    result = evaluate_coverage(load(raw))
    assert result.primary_disposition == "INSUFFICIENT_EVIDENCE"
    assert reason in {f.reason_code for f in result.findings}
    assert result.coverage.exercised_scenarios == 2


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"method": "narrative"}, "NARRATIVE_IS_NOT_EXECUTION"),
        ({"scenario_id": "OTHER"}, "WITNESS_SCENARIO_MISMATCH"),
        ({"method": "fake"}, "MALFORMED_WITNESS"),
        ({"extra": "hidden instruction"}, "MALFORMED_WITNESS"),
        ({"run_id": ""}, "MALFORMED_WITNESS"),
    ],
)
def test_witness_validation(raw, change, reason):
    rewrite(raw["evidence"][1], **change)
    result = evaluate_coverage(load(raw))
    assert result.primary_disposition == "INSUFFICIENT_EVIDENCE"
    assert reason in {f.reason_code for f in result.findings}


@pytest.mark.parametrize("body", ["not json", '{"actual":"a","actual":"b"}', "[1]", "NaN"])
def test_malformed_witness(raw, body):
    raw["evidence"][0].update(content=body, sha256=sha256(body))
    assert evaluate_coverage(load(raw)).primary_disposition == "INSUFFICIENT_EVIDENCE"


def test_hash_blocker(raw):
    raw["evidence"][1]["content"] += " "
    result = evaluate_coverage(load(raw))
    assert result.primary_disposition == "HOLD"
    assert "EVIDENCE_HASH_MISMATCH" in {f.reason_code for f in result.findings}


def test_conflicting_observations(raw):
    conflict = copy.deepcopy(raw["evidence"][1])
    conflict["id"] = "EV-CONFLICT"
    rewrite(conflict, actual="allowed")
    raw["evidence"].append(conflict)
    result = evaluate_coverage(load(raw))
    assert result.primary_disposition == "HOLD"
    assert result.coverage.satisfied_scenarios == 2


def test_mode_omission_is_not_hidden(raw):
    raw["claims"][0]["scenarios"] = raw["claims"][0]["scenarios"][:1]
    raw["evidence"] = raw["evidence"][:1]
    result = derive_requirements(load(raw))
    assert result.primary_disposition == "INSUFFICIENT_EVIDENCE"
    assert result.coverage.missing_mode_obligations == 2
    assert all(r.kind == "collect_evidence" for r in result.requirements)


def test_precedence_and_no_suppression(raw):
    raw["claims"][0]["scenarios"][0]["semantic"] = True
    rewrite(raw["evidence"][0], actual="denied")
    rewrite(raw["evidence"][1], actual="allowed")
    raw["evidence"].pop()
    result = evaluate_coverage(load(raw))
    assert result.primary_disposition == "SEMANTIC_DRIFT_DETECTED"
    assert {f.disposition for f in result.findings} == {
        "SEMANTIC_DRIFT_DETECTED",
        "UPDATE_REQUIRED",
        "INSUFFICIENT_EVIDENCE",
    }
    raw["evidence"][1]["content"] += " "
    assert evaluate_coverage(load(raw)).primary_disposition == "HOLD"


def test_requirement_identity_and_evidence_binding(raw):
    rewrite(raw["evidence"][1], actual="allowed")
    first = derive_requirements(load(raw))
    raw["baseline_version"] = "new"
    for ev in raw["evidence"]:
        ev["baseline_version"] = "new"
    second = derive_requirements(load(raw))
    assert first.requirements[0].id == second.requirements[0].id
    assert first.contract_sha256 != second.contract_sha256
    assert first.requirements[0].baseline_evidence_refs == ("EV-1",)


def test_replay_and_cross_call_isolation(contract, raw):
    expected = derive_requirements(contract).model_dump_json()
    with ThreadPoolExecutor(max_workers=4) as pool:
        outputs = list(pool.map(lambda _: derive_requirements(contract).model_dump_json(), range(12)))
    assert set(outputs) == {expected}
    raw["evidence"] = []
    assert evaluate_coverage(load(raw)).primary_disposition == "INSUFFICIENT_EVIDENCE"
    assert derive_requirements(contract).model_dump_json() == expected


def test_repeated_bad_records_preserve_all_refs(raw):
    raw["evidence"][0]["content"] += " "
    ev = copy.deepcopy(raw["evidence"][0])
    ev["id"] = "EV-OTHER"
    raw["evidence"].append(ev)
    result = evaluate_coverage(load(raw))
    item = next(f for f in result.findings if f.reason_code == "EVIDENCE_HASH_MISMATCH")
    assert item.evidence_refs == ("EV-0", "EV-OTHER")
