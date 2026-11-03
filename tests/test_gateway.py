import pytest
from fastapi.testclient import TestClient

from hmt_mission_gateway.application import create_apps
from hmt_mission_gateway.settings import Settings, read_secret

TOKEN = "test-only-not-a-live-credential-00000000"


@pytest.fixture
def settings(tmp_path):
    token = tmp_path / "token"
    token.write_text(TOKEN)
    token.chmod(0o600)
    metric_token = tmp_path / "metric-token"
    metric_token.write_text(TOKEN + "-metrics")
    metric_token.chmod(0o600)
    return Settings(token_file=token, metrics_token_file=metric_token, allowed_hosts=["testserver"])


def headers():
    return {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json, text/event-stream"}


def request(client, method, params, call_id=1):
    return client.post(
        "/mcp", headers=headers(), json={"jsonrpc": "2.0", "id": call_id, "method": method, "params": params}
    )


def test_real_wire_tools_metrics(settings, raw):
    app, monitor = create_apps(settings)
    with TestClient(app) as client, TestClient(monitor) as metrics:
        response = request(
            client,
            "initialize",
            {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1"},
            },
        )
        assert response.status_code == 200, response.text
        assert "serverInfo" in response.json()["result"]
        listed = request(client, "tools/list", {}).json()["result"]["tools"]
        assert len(listed) == 4
        for tool in listed:
            response = request(client, "tools/call", {"name": tool["name"], "arguments": {"contract": raw}})
            assert response.status_code == 200, response.text
            assert not response.json()["result"]["isError"]
        bad = request(client, "tools/call", {"name": "inspect_baseline", "arguments": {}})
        assert bad.json()["result"]["isError"]
        response = metrics.get("/metrics", headers={"Authorization": f"Bearer {TOKEN}-metrics"})
        assert response.status_code == 200
        assert 'hmt_mcp_tool_calls_total{status="success",tool="inspect_baseline"} 1.0' in response.text
        assert 'hmt_mcp_tool_calls_total{status="error",tool="inspect_baseline"} 1.0' in response.text
        assert client.get("/skills/hmt-mission-assurance", headers=headers()).status_code == 200


def test_negative_http(settings):
    app, metrics = create_apps(settings)
    with TestClient(app) as client, TestClient(metrics) as monitor:
        assert client.get("/health/live").status_code == 401
        assert monitor.get("/metrics").status_code == 401
        assert client.get("/health/live", headers=headers()).status_code == 200
        assert client.get("/health/live", headers={**headers(), "Origin": "https://evil"}).status_code == 403
        assert client.get("/health/live", headers={**headers(), "Host": "evil"}).status_code == 400
        assert client.get("/docs", headers=headers()).status_code == 404
        assert client.get("/metrics", headers=headers()).status_code == 404
        assert monitor.get("/mcp", headers={"Authorization": f"Bearer {TOKEN}-metrics"}).status_code == 404
        large = client.post("/mcp", headers=headers(), content="x" * (settings.max_body_bytes + 1))
        assert large.status_code == 413


def test_secrets_fail_closed(settings, tmp_path):
    settings.token_file.write_text("short")
    with pytest.raises(ValueError, match="SECRET_FORMAT"):
        create_apps(settings)
    link = tmp_path / "link"
    link.symlink_to(settings.token_file)
    with pytest.raises(ValueError, match="SECRET_SYMLINK"):
        read_secret(link)


def test_metric_exception_unknown_cardinality():
    from prometheus_client import generate_latest

    from hmt_mission_gateway.metrics import Metrics

    def fail(name, arguments):
        raise RuntimeError("PRIVATE")

    metrics = Metrics()
    result = metrics.execute("untrusted-name-123", {}, fail)
    assert result.isError and "PRIVATE" not in str(result)
    metrics.execute("untrusted-name-456", {})
    text = generate_latest(metrics.registry).decode()
    assert "untrusted-name" not in text
    assert 'status="exception",tool="unknown"' in text
    assert "hmt_mcp_inflight 0.0" in text


def test_secret_capabilities_are_separate(settings):
    app, metrics = create_apps(settings)
    with TestClient(app) as client, TestClient(metrics) as monitor:
        assert (
            client.get("/health/live", headers={"Authorization": f"Bearer {TOKEN}-metrics"}).status_code
            == 401
        )
        assert monitor.get("/metrics", headers=headers()).status_code == 401
    settings.metrics_token_file.write_text(TOKEN)
    with pytest.raises(ValueError, match="SECRETS_MUST_DIFFER"):
        create_apps(settings)
