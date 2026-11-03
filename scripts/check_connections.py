"""Exercise shipped host launch profiles; do not impersonate signed-in host clients."""

import asyncio
import copy
import json
import os
import subprocess
import tempfile
import tomllib
from datetime import UTC, datetime
from pathlib import Path

from jsonschema import validate
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from hmt_mission_assurance import __version__
from hmt_mission_assurance.server import TOOLS

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {
    "claude-code": ("claude-code.mcp.json", "mcpServers"),
    "cursor": ("cursor.mcp.json", "mcpServers"),
    "codex-cli": ("codex.config.toml", "mcp_servers"),
    "github-copilot-agent-mode": ("copilot.mcp.json", "servers"),
}


def profile_command(filename: str, key: str, executable: Path) -> StdioServerParameters:
    path = ROOT / "integrations" / filename
    document = tomllib.loads(path.read_text()) if path.suffix == ".toml" else json.loads(path.read_text())
    entry = document[key]["hmt-mission-assurance"]
    assert entry["command"] == "hmt-mission-assurance-mcp" and entry["args"] == []
    assert "url" not in entry and "env" not in entry
    if key != "mcp_servers":
        assert entry["type"] == "stdio"
    # Resolve the configured console command to this isolated wheel installation.
    return StdioServerParameters(command=str(executable), args=entry["args"])


async def check_session(params: StdioServerParameters, raw: dict, cwd: Path) -> dict:
    params.cwd = str(cwd)
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools = (await session.list_tools()).tools
        assert {tool.name for tool in tools} == set(TOOLS)
        results = {}
        for tool in tools:
            annotations = tool.annotations
            assert annotations and annotations.readOnlyHint and annotations.idempotentHint
            assert annotations.destructiveHint is False and annotations.openWorldHint is False
            assert tool.outputSchema and tool.inputSchema
            result = await session.call_tool(tool.name, {"contract": raw})
            assert not result.isError and result.structuredContent
            validate(result.structuredContent, tool.outputSchema)
            results[tool.name] = result.structuredContent
        expected = results["evaluate_coverage"]
        assert expected["primary_disposition"] == "STABLE_AS_IS"
        assert expected["evaluator_version"] == __version__
        altered = copy.deepcopy(raw)
        altered["evidence"] = []
        changed = await session.call_tool("evaluate_coverage", {"contract": altered})
        assert changed.structuredContent
        assert changed.structuredContent["primary_disposition"] == "INSUFFICIENT_EVIDENCE"
        for name, arguments in (
            ("evaluate_coverage", {}),
            ("evaluate_coverage", {"contract": raw, "secret": "NEVER-ECHO-SENTINEL"}),
            ("unknown_tool", {}),
        ):
            error = await session.call_tool(name, arguments)
            assert error.isError and "NEVER-ECHO-SENTINEL" not in str(error)
        replay = await session.call_tool("evaluate_coverage", {"contract": raw})
        assert replay.structuredContent == expected
        report = results["emit_delta_report"]
        assert {k: v for k, v in report["evaluation"].items() if k != "graph"} == {
            k: v for k, v in expected.items() if k != "graph"
        }
        assert report["evaluation"]["graph"]["nodes"]
        assert report["markdown"] and "<!doctype html>" in report["html"]
    return expected


def check_cli(cli: Path, base: Path) -> dict:
    def invoke(*arguments: str) -> subprocess.CompletedProcess:
        return subprocess.run([str(cli), *arguments], cwd=base, capture_output=True, text=True, timeout=30)

    schema = invoke("schema")
    starter = invoke("example")
    assert schema.returncode == starter.returncode == 0
    validate(json.loads(starter.stdout), json.loads(schema.stdout))
    stable = invoke("evaluate", str(ROOT / "examples/after.json"))
    assert stable.returncode == 0
    assert json.loads(stable.stdout)["primary_disposition"] == "STABLE_AS_IS"
    destination = base / "reports"
    findings = invoke("evaluate", str(ROOT / "examples/before.json"), "--out", str(destination))
    assert findings.returncode == 2
    assert {p.name for p in destination.iterdir()} == {
        "evaluation.json",
        "delta-report.md",
        "delta-report.html",
    }
    assert (
        json.loads((destination / "evaluation.json").read_text())["primary_disposition"]
        == "INSUFFICIENT_EVIDENCE"
    )
    assert (destination / "delta-report.md").read_text() and "<!doctype html>" in (
        destination / "delta-report.html"
    ).read_text()
    before = {p.name: p.read_bytes() for p in destination.iterdir()}
    assert invoke("evaluate", str(ROOT / "examples/before.json"), "--out", str(destination)).returncode == 3
    assert {p.name: p.read_bytes() for p in destination.iterdir()} == before
    assert invoke("evaluate", str(base / "missing.json")).returncode == 3
    return {
        "schema_and_example": "PASS",
        "exit_codes": [0, 2, 3],
        "report_outputs": "PASS",
        "refuse_overwrite": "PASS",
    }


async def check_connections(executable: Path, cli: Path, base: Path) -> dict:
    raw = json.loads((ROOT / "examples/after.json").read_text())
    checks = []
    for host, (filename, key) in PROFILES.items():
        cwd = base / host
        cwd.mkdir()
        async with asyncio.timeout(30):
            expected = await check_session(profile_command(filename, key, executable), raw, cwd)
        assert not list(cwd.iterdir()), "MCP wrote into its working directory"
        checks.append(
            {"host": host, "profile": "integrations/" + filename, "status": "PASS", "tools": sorted(TOOLS)}
        )
    restart = base / "restart"
    restart.mkdir()
    async with asyncio.timeout(30):
        repeated = await check_session(StdioServerParameters(command=str(cli), args=["serve"]), raw, restart)
    assert repeated == expected and not list(restart.iterdir())
    cli_base = base / "cli-check"
    cli_base.mkdir()
    return {
        "version": __version__,
        "recorded_at": datetime.now(UTC).isoformat(),
        "status": "PASS",
        "transport": "stdio",
        "checks": checks,
        "cli": check_cli(cli, cli_base),
        "cross_call_and_restart_replay": "PASS",
        "invalid_input_recovery": "PASS",
        "host_ui_validation": "NOT_RUN: signed-in Claude Code, Cursor, Codex CLI, and Copilot clients unavailable",
        "scope": "MCP SDK client launching the installed wheel using each parsed host profile; no target code executed",
        "read_only_limit": "Empty working directories checked; not an OS sandbox or exhaustive filesystem/network trace",
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bin-dir", required=True, type=Path, help="Installed tool executables")
    args = parser.parse_args()
    suffix = ".exe" if os.name == "nt" else ""
    with tempfile.TemporaryDirectory() as directory:
        result = asyncio.run(
            check_connections(
                (args.bin_dir / ("hmt-mission-assurance-mcp" + suffix)).resolve(),
                (args.bin_dir / ("hmt-mission-assurance" + suffix)).resolve(),
                Path(directory),
            )
        )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
