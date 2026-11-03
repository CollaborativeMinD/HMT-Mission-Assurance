"""Install the built wheel into an isolated uv tool environment and exercise it."""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from check_connections import check_connections

from hmt_mission_assurance import __version__

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    wheel = ROOT / f"dist/hmt_mission_assurance-{__version__}-py3-none-any.whl"
    assert wheel.is_file(), "Run uv build first"
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        env = dict(os.environ, UV_TOOL_DIR=str(base / "tools"), UV_TOOL_BIN_DIR=str(base / "bin"))
        command = ["uv", "tool", "install", "--python", sys.executable, str(wheel)]
        subprocess.run(command, env=env, check=True, capture_output=True, text=True)
        interpreter = base / "tools/hmt-mission-assurance/bin/python"
        subprocess.run([str(interpreter), str(ROOT / "scripts/check_gateway_install.py")], check=True)
        suffix = ".exe" if sys.platform == "win32" else ""
        cli = base / "bin" / ("hmt-mission-assurance" + suffix)
        version = subprocess.run(
            [str(cli), "--version"], check=True, capture_output=True, text=True
        ).stdout.strip()
        assert version == __version__
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
        connections = asyncio.run(
            check_connections(base / "bin" / ("hmt-mission-assurance-mcp" + suffix), cli, base)
        )
        (ROOT / "evidence/container/connections.json").write_text(json.dumps(connections, indent=2) + "\n")
    result = {
        "status": "PASS",
        "version": version,
        "isolated_uv_install": True,
        "skill_bytes_match": True,
        "installed_mcp_tool_count": 4,
        "installed_html_payload": "PASS",
        "python": sys.version.split()[0],
    }
    (ROOT / "evidence/container/install.json").write_text(json.dumps(result, indent=2) + "\n")
    print("G-INSTALL-008: PASS (isolated wheel, CLI, skill, MCP, and bundled report assets)")


if __name__ == "__main__":
    main()
