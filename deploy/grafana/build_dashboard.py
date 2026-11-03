"""Validate a deliberately small dashboard contract and emit Grafana JSON."""

import argparse
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ROOT = Path(__file__).resolve().parent


class PanelSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    title: str = Field(min_length=1, max_length=100)
    expression: str = Field(min_length=1, max_length=500)
    legend: str = Field(min_length=1, max_length=100)
    unit: Literal["short", "ops", "s", "percentunit"] = "short"


class DashboardSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    version: Literal[1]
    uid: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,40}$")
    title: str = Field(min_length=1, max_length=100)
    panels: list[PanelSpec] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def unique_titles(self) -> "DashboardSpec":
        if len({panel.title for panel in self.panels}) != len(self.panels):
            raise ValueError("Panel titles must be unique")
        return self


def render_panel(panel: PanelSpec, index: int) -> dict:
    return {
        "id": index + 1,
        "type": "timeseries",
        "title": panel.title,
        "datasource": {"type": "prometheus", "uid": "hmt-prometheus"},
        "gridPos": {"h": 8, "w": 12, "x": (index % 2) * 12, "y": (index // 2) * 8},
        "targets": [{"refId": "A", "expr": panel.expression, "legendFormat": panel.legend}],
        "fieldConfig": {"defaults": {"unit": panel.unit}, "overrides": []},
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}},
    }


def render_dashboard(spec: DashboardSpec) -> dict:
    return {
        "uid": spec.uid,
        "title": spec.title,
        "schemaVersion": 39,
        "version": 1,
        "editable": False,
        "tags": ["hmt", "mcp", "local-only"],
        "timezone": "browser",
        "refresh": "15s",
        "time": {"from": "now-1h", "to": "now"},
        "panels": [render_panel(panel, index) for index, panel in enumerate(spec.panels)],
        "annotations": {"list": []},
        "templating": {"list": []},
    }


def artifacts() -> dict[Path, dict]:
    spec = DashboardSpec.model_validate_json((ROOT / "dashboard.spec.json").read_text())
    return {
        ROOT / "dashboard.schema.json": DashboardSpec.model_json_schema(),
        ROOT / "dashboards/hmt-mcp.json": render_dashboard(spec),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for path, content in artifacts().items():
        if args.check:
            if json.loads(path.read_text()) != content:
                raise SystemExit(f"Generated artifact differs: {path.name}")
        else:
            path.write_text(json.dumps(content, indent=2) + "\n")
    print("Dashboard schema and generated JSON match" if args.check else "Dashboard artifacts generated")


if __name__ == "__main__":
    main()
