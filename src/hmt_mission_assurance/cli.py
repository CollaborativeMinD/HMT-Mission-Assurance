"""Explicit local artifact I/O lives here, outside the read-only MCP surface."""

import argparse
import json
import os
from importlib.resources import files
from pathlib import Path

from . import __version__
from .contract import EvaluationContract
from .encoding import MAX_INPUT_BYTES, canonical, parse_json
from .reports import emit_delta_report


def read_contract(path: Path) -> EvaluationContract:
    with path.open("rb") as stream:
        raw = stream.read(MAX_INPUT_BYTES + 1)
    value = parse_json(raw.decode("utf-8"))
    return EvaluationContract.model_validate_json(canonical(value))


def write_reports(contract: EvaluationContract, destination: Path) -> str:
    bundle = emit_delta_report(contract)
    destination.mkdir(parents=True, exist_ok=False)
    contents = {
        "delta-report.md": bundle.markdown,
        "delta-report.html": bundle.html,
        "evaluation.json": json.dumps(bundle.evaluation.model_dump(mode="json"), indent=2) + "\n",
    }
    for name, content in contents.items():
        with (destination / name).open("x", encoding="utf-8") as stream:
            stream.write(content)
    return bundle.evaluation.primary_disposition


def skill_text() -> str:
    resource = files("hmt_mission_assurance").joinpath("data/SKILL.md")
    if resource.is_file():
        return resource.read_text(encoding="utf-8")
    return (Path(__file__).resolve().parents[2] / "SKILL.md").read_text(encoding="utf-8")


def install_skill(parent: Path) -> Path:
    destination = parent / "hmt-mission-assurance"
    content = skill_text()
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "SKILL.md").write_text(content, encoding="utf-8")
    return destination


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="hmt-mission-assurance", description="Determine what supplied engineering evidence supports."
    )
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("serve", help="Run the read-only stdio MCP interface")
    commands.add_parser("schema", help="Print the public input JSON Schema")
    commands.add_parser("example", help="Print the bundled before example contract")
    evaluate = commands.add_parser(
        "evaluate", help="Evaluate a supplied contract without running target code"
    )
    evaluate.add_argument("contract", type=Path)
    evaluate.add_argument("--out", type=Path, help="Create a new directory with JSON, Markdown, and HTML")
    install = commands.add_parser("install-skill", help="Install the single SKILL.md for an agent")
    default = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "skills"
    install.add_argument(
        "--dest", type=Path, default=default, help="Skill parent directory; refuses replacement"
    )
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "serve":
            from .server import main as serve

            serve()
        elif args.command == "schema":
            print(json.dumps(EvaluationContract.model_json_schema(), indent=2))
        elif args.command == "example":
            print(files("hmt_mission_assurance").joinpath("data/example.json").read_text())
        elif args.command == "install-skill":
            print(install_skill(args.dest))
        elif args.command == "evaluate":
            contract = read_contract(args.contract)
            if args.out:
                disposition = write_reports(contract, args.out)
                print(disposition)
            else:
                result = emit_delta_report(contract).evaluation
                print(json.dumps(result.model_dump(mode="json"), indent=2))
                disposition = result.primary_disposition
            return 0 if disposition == "STABLE_AS_IS" else 2
    except (OSError, ValueError, RecursionError):
        print("INVALID_INPUT_OR_DESTINATION: check the contract and choose a new output directory.")
        return 3
    return 0
