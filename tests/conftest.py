import copy
import json
from pathlib import Path

import pytest

from hmt_mission_assurance.contract import EvaluationContract
from hmt_mission_assurance.encoding import canonical

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def raw() -> dict:
    return copy.deepcopy(json.loads((ROOT / "examples/after.json").read_text()))


@pytest.fixture
def contract(raw: dict) -> EvaluationContract:
    return EvaluationContract.model_validate_json(canonical(raw))
