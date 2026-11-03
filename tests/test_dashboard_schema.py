"""Regression witnesses for the deployment dashboard contract."""

import importlib.util
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "deploy/grafana/build_dashboard.py"
MODULE_SPEC = importlib.util.spec_from_file_location("hmt_dashboard_builder", MODULE_PATH)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
builder = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(builder)


def test_generated_artifacts_match_contract():
    for path, expected in builder.artifacts().items():
        assert json.loads(path.read_text()) == expected


def test_dashboard_rejects_unknown_fields():
    value = {"version": 1, "uid": "test", "title": "Test", "panels": [], "secret": "no"}
    with pytest.raises(ValidationError):
        builder.DashboardSpec.model_validate(value)


def test_dashboard_rejects_invalid_unit_and_empty_query():
    with pytest.raises(ValidationError):
        builder.PanelSpec(title="Test", expression="", legend="Test", unit="password")


def test_dashboard_rejects_duplicate_panel_titles():
    panel = {"title": "Test", "expression": "up", "legend": "up"}
    with pytest.raises(ValidationError, match="unique"):
        builder.DashboardSpec.model_validate(
            {"version": 1, "uid": "test", "title": "Test", "panels": [panel, panel]}
        )


def test_dashboard_uses_fixed_provisioned_datasource():
    dashboard = builder.artifacts()[ROOT / "deploy/grafana/dashboards/hmt-mcp.json"]
    assert dashboard["editable"] is False
    assert len(dashboard["panels"]) == 6
    for panel in dashboard["panels"]:
        assert panel["datasource"] == {"type": "prometheus", "uid": "hmt-prometheus"}
        assert panel["targets"][0]["expr"]


def test_error_fraction_includes_unexpected_exceptions():
    dashboard = builder.artifacts()[ROOT / "deploy/grafana/dashboards/hmt-mcp.json"]
    panel = next(panel for panel in dashboard["panels"] if panel["title"] == "Tool error fraction")
    assert 'status=~"error|exception"' in panel["targets"][0]["expr"]
