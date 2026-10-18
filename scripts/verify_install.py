"""Install the built wheel into an isolated uv tool environment and exercise it."""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]


async def check_installed_mcp(executable: Path, contract: dict) -> int:
    params = StdioServerParameters(command=str(executable), args=[])
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools = (await session.list_tools()).tools
        assert len(tools) == 4
        response = await session.call_tool("emit_delta_report", {"contract": contract})
        assert not response.isError and response.structuredContent
        assert "<!doctype html>" in response.structuredContent["html"]
    return len(tools)


def main() -> None:
    wheel = ROOT / "dist/hmt_mission_assurance-0.1.0-py3-none-any.whl"
    assert wheel.is_file(), "Run uv build first"
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        env = dict(os.environ, UV_TOOL_DIR=str(base / "tools"), UV_TOOL_BIN_DIR=str(base / "bin"))
        command = ["uv", "tool", "install", "--python", sys.executable, str(wheel)]
        subprocess.run(command, env=env, check=True, capture_output=True, text=True)
        suffix = ".exe" if sys.platform == "win32" else ""
        cli = base / "bin" / ("hmt-mission-assurance" + suffix)
        version = subprocess.run(
            [str(cli), "--version"], check=True, capture_output=True, text=True
        ).stdout.strip()
        assert version == "0.1.0"
        subprocess.run(
            [str(cli), "install-skill", "--dest", str(base / "skills")], check=True, capture_output=True
        )
        installed = base / "skills/hmt-mission-assurance/SKILL.md"
        assert installed.read_bytes() == (ROOT / "SKILL.md").read_bytes()
        report = base / "reports"
        completed = subprocess.run(
            [str(cli), "evaluate", str(ROOT / "examples/before.json"), "--out", str(report)],
            capture_output=True,
        )
        assert completed.returncode == 2
        assert "INSUFFICIENT_EVIDENCE" in (report / "evaluation.json").read_text()
        contract = json.loads((ROOT / "examples/after.json").read_text())
        count = asyncio.run(
            check_installed_mcp(base / "bin" / ("hmt-mission-assurance-mcp" + suffix), contract)
        )
    result = {
        "status": "PASS",
        "version": version,
        "isolated_uv_install": True,
        "skill_bytes_match": True,
        "installed_mcp_tool_count": count,
        "installed_html_rendering": "PASS",
        "python": sys.version.split()[0],
    }
    (ROOT / "evidence/install.json").write_text(json.dumps(result, indent=2) + "\n")
    print("G-INSTALL-008: PASS (isolated wheel, CLI, skill, MCP, and bundled report assets)")


if __name__ == "__main__":
    main()
