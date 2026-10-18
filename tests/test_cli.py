import json
import sys
from pathlib import Path

from hmt_mission_assurance import cli
from hmt_mission_assurance.encoding import MAX_INPUT_BYTES

ROOT = Path(__file__).resolve().parents[1]


def invoke(monkeypatch, *arguments):
    monkeypatch.setattr(sys, "argv", ["hmt-mission-assurance", *map(str, arguments)])
    return cli.main()


def test_schema_and_example(monkeypatch, capsys):
    assert invoke(monkeypatch, "schema") == 0
    assert json.loads(capsys.readouterr().out)["title"] == "EvaluationContract"
    assert invoke(monkeypatch, "example") == 0
    assert json.loads(capsys.readouterr().out)["tool_id"] == "example-gateway"


def test_report_outputs_and_exit_codes(monkeypatch, tmp_path, capsys):
    destination = tmp_path / "report"
    assert invoke(monkeypatch, "evaluate", ROOT / "examples/before.json", "--out", destination) == 2
    assert {p.name for p in destination.iterdir()} == {
        "evaluation.json",
        "delta-report.md",
        "delta-report.html",
    }
    assert invoke(monkeypatch, "evaluate", ROOT / "examples/before.json", "--out", destination) == 3
    assert invoke(monkeypatch, "evaluate", ROOT / "examples/after.json") == 0
    assert invoke(monkeypatch, "evaluate", ROOT / "examples/before.json") == 2
    assert "INSUFFICIENT_EVIDENCE" in capsys.readouterr().out


def test_invalid_input_and_limits(monkeypatch, tmp_path):
    assert invoke(monkeypatch, "evaluate", tmp_path / "missing") == 3
    path = tmp_path / "invalid.json"
    path.write_text('{"a":1,"a":2}')
    assert invoke(monkeypatch, "evaluate", path) == 3
    path.write_text("x" * (MAX_INPUT_BYTES + 2))
    assert invoke(monkeypatch, "evaluate", path) == 3


def test_install_skill_refuses_replacement(monkeypatch, tmp_path):
    assert invoke(monkeypatch, "install-skill", "--dest", tmp_path) == 0
    installed = tmp_path / "hmt-mission-assurance/SKILL.md"
    assert installed.read_text() == (ROOT / "SKILL.md").read_text()
    assert invoke(monkeypatch, "install-skill", "--dest", tmp_path) == 3


def test_skill_fallback(monkeypatch):
    class MissingResource:
        def joinpath(self, path):
            return self

        def is_file(self):
            return False

    monkeypatch.setattr(cli, "files", lambda package: MissingResource())
    assert cli.skill_text() == (ROOT / "SKILL.md").read_text()


def test_serve_branch(monkeypatch):
    called = []
    monkeypatch.setattr("hmt_mission_assurance.server.main", lambda: called.append(True))
    assert invoke(monkeypatch, "serve") == 0 and called
