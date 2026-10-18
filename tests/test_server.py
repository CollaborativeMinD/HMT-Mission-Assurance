import asyncio
import copy
import sys

from jsonschema import validate
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from hmt_mission_assurance.encoding import MAX_INPUT_BYTES
from hmt_mission_assurance.server import TOOLS, dispatch


def test_four_tools_and_redacted_rejection(raw):
    assert set(TOOLS) == {"inspect_baseline", "evaluate_coverage", "derive_requirements", "emit_delta_report"}
    for name in TOOLS:
        result = dispatch(name, {"contract": raw})
        assert not result.isError and result.structuredContent
        validate(result.structuredContent, TOOLS[name][1].model_json_schema())
    secret = "PRIVATE-DO-NOT-ECHO"
    result = dispatch("inspect_baseline", {"contract": raw, "unexpected": secret})
    assert result.isError and secret not in str(result)
    assert dispatch("execute", {"command": "anything"}).isError


def test_application_input_limit(raw):
    assert dispatch("inspect_baseline", {"x": "a" * MAX_INPUT_BYTES}).isError
    assert dispatch("inspect_baseline", {"x": float("nan")}).isError
    raw["evidence"][0]["content"] = "x" * 16001
    assert dispatch("inspect_baseline", {"contract": raw}).isError


def test_source_reference_never_fetches(raw, tmp_path, monkeypatch):
    hidden = tmp_path / "hidden.txt"
    hidden.write_text("UNREAD-CONTENT-SENTINEL")
    raw["evidence"][0]["source_ref"] = str(hidden)

    def deny(*args, **kwargs):
        raise AssertionError("Target I/O attempted")

    monkeypatch.setattr("builtins.open", deny)
    monkeypatch.setattr("socket.create_connection", deny)
    monkeypatch.setattr("subprocess.run", deny)
    for name in ("inspect_baseline", "evaluate_coverage", "derive_requirements"):
        result = dispatch(name, {"contract": raw})
        assert not result.isError and "UNREAD-CONTENT-SENTINEL" not in str(result)


def test_call_is_recomputed(raw):
    prior = dispatch("evaluate_coverage", {"contract": raw})
    changed = copy.deepcopy(raw)
    changed["evidence"] = []
    result = dispatch("evaluate_coverage", {"contract": changed})
    assert result.structuredContent
    assert result.structuredContent["primary_disposition"] == "INSUFFICIENT_EVIDENCE"
    assert dispatch("evaluate_coverage", {"contract": raw}) == prior


def test_stdio_protocol(raw):
    async def campaign():
        params = StdioServerParameters(command=sys.executable, args=["-m", "hmt_mission_assurance.server"])
        async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            assert {t.name for t in tools} == set(TOOLS)
            for tool in tools:
                assert tool.annotations
                assert tool.annotations.readOnlyHint and not tool.annotations.openWorldHint
                assert tool.outputSchema
                result = await session.call_tool(tool.name, {"contract": raw})
                assert not result.isError and result.structuredContent
                validate(result.structuredContent, tool.outputSchema)
            malformed = await session.call_tool("evaluate_coverage", {"contract": raw, "command": "ignored?"})
            assert malformed.isError
            unknown = await session.call_tool("arbitrary_command", {})
            assert unknown.isError

    asyncio.run(campaign())
