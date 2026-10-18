"""Exactly four read-only tools, over stdio. No filesystem or network adapters."""

import asyncio
from typing import Any

from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, TextContent, Tool, ToolAnnotations
from pydantic import ValidationError

from .contract import ToolRequest
from .encoding import MAX_INPUT_BYTES, canonical
from .engine import derive_requirements, evaluate_coverage
from .evidence import inspect_baseline
from .reports import emit_delta_report
from .results import BaselineInspection, EvaluationResult, ReportBundle

TOOLS = {
    "inspect_baseline": (
        inspect_baseline,
        BaselineInspection,
        "Establish what supplied baseline witnesses demonstrate.",
    ),
    "evaluate_coverage": (
        evaluate_coverage,
        EvaluationResult,
        "Expose unsupported claims, gaps, and contradictions.",
    ),
    "derive_requirements": (
        derive_requirements,
        EvaluationResult,
        "Derive falsifiable obligations from evidenced or unresolved gaps.",
    ),
    "emit_delta_report": (
        emit_delta_report,
        ReportBundle,
        "Return JSON, Markdown, and offline HTML; write nothing.",
    ),
}


def error_result(code: str) -> CallToolResult:
    return CallToolResult(isError=True, content=[TextContent(type="text", text=code)])


def dispatch(name: str, arguments: dict[str, Any]) -> CallToolResult:
    """Validate every call afresh and redact input values from errors."""
    if name not in TOOLS:
        return error_result("UNKNOWN_TOOL")
    try:
        raw = canonical(arguments)
        if len(raw.encode()) > MAX_INPUT_BYTES:
            return error_result("INPUT_TOO_LARGE")
        request = ToolRequest.model_validate_json(raw)
        output = TOOLS[name][0](request.contract)
        payload = output.model_dump(mode="json")
        return CallToolResult(
            isError=False,
            structuredContent=payload,
            content=[TextContent(type="text", text=canonical(payload))],
        )
    except (ValidationError, ValueError, TypeError, RecursionError):
        return error_result("INVALID_CONTRACT")


def create_server() -> Server:
    server = Server("hmt-mission-assurance")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name=name,
                description=entry[2],
                inputSchema=ToolRequest.model_json_schema(),
                outputSchema=entry[1].model_json_schema(),
                annotations=ToolAnnotations(
                    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
                ),
            )
            for name, entry in TOOLS.items()
        ]

    @server.call_tool(validate_input=False)
    async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
        return dispatch(name, arguments)

    return server


async def run_stdio() -> None:
    server = create_server()
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    asyncio.run(run_stdio())


if __name__ == "__main__":
    main()
