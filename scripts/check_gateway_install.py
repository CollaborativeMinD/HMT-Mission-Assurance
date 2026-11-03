"""Exercise installed-wheel authenticated skill and actual MCP discovery."""

import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from hmt_mission_gateway.application import create_apps
from hmt_mission_gateway.settings import Settings


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        mcp, metrics = Path(directory) / "mcp", Path(directory) / "metrics"
        mcp.write_text("wheel-test-only-mcp-token-000000000000")
        metrics.write_text("wheel-test-only-metrics-token-00000000")
        mcp.chmod(0o600)
        metrics.chmod(0o600)
        settings = Settings(token_file=mcp, metrics_token_file=metrics, allowed_hosts=["testserver"])
        app, _ = create_apps(settings)
        headers = {
            "Authorization": "Bearer " + mcp.read_text(),
            "Accept": "application/json, text/event-stream",
        }
        with TestClient(app) as client:
            skill = client.get("/skills/hmt-mission-assurance", headers=headers)
            assert skill.status_code == 200 and "name: hmt-mission-assurance" in skill.text
            listed = client.post(
                "/mcp",
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {},
                },
            )
            assert listed.status_code == 200
            assert len(listed.json()["result"]["tools"]) == 4
    print("INSTALLED_GATEWAY: PASS (wheel skill and real MCP discovery)")


if __name__ == "__main__":
    main()
