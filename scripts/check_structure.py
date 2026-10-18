"""Static architecture, generated-schema, skill, and bounded-function gates."""

import ast
import json
import re
from pathlib import Path

from hmt_mission_assurance.contract import EvaluationContract

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    skills = [
        p for p in ROOT.rglob("SKILL.md") if not any(x.startswith(".") for x in p.relative_to(ROOT).parts)
    ]
    assert skills == [ROOT / "SKILL.md"], "Exactly one repository SKILL.md is required"
    text = skills[0].read_text()
    assert text.startswith("---\nname: hmt-mission-assurance\ndescription:")
    assert text.count("\n---\n") == 1
    assert len(text.splitlines()) < 500
    assert (
        json.loads((ROOT / "schemas/evaluation-contract.schema.json").read_text())
        == EvaluationContract.model_json_schema()
    )
    banned = {"subprocess", "socket", "requests", "httpx", "urllib", "os", "pathlib"}
    production = list((ROOT / "src").rglob("*.py"))
    for path in production + list((ROOT / "scripts").glob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                assert node.end_lineno is not None
                assert node.end_lineno - node.lineno + 1 <= 60, f"Function too long: {path.name}:{node.name}"
            if (
                path in production
                and path.name != "cli.py"
                and isinstance(node, (ast.Import, ast.ImportFrom))
            ):
                modules = (
                    [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                )
                assert not {m.split(".")[0] for m in modules} & banned, f"Target I/O adapter: {path}"
    for path in production + list((ROOT / "tests").glob("*.py")):
        assert not re.search(
            r"pytest\.mark\.(skip|xfail)|noqa|pragma: no cover|type: ignore", path.read_text()
        )
    print("G-ARCH-001 / G-SCHEMA-002 / G-SKILL-003: PASS")


if __name__ == "__main__":
    main()
