"""Bounded-cardinality measurements around real tool dispatch."""

from collections.abc import Callable
from time import perf_counter
from typing import Any

from mcp.types import CallToolResult
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

from hmt_mission_assurance.server import TOOLS, dispatch, error_result


class Metrics:
    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self.calls = Counter(
            "hmt_mcp_tool_calls_total", "Completed tool calls", ["tool", "status"], registry=self.registry
        )
        self.latency = Histogram(
            "hmt_mcp_tool_execution_seconds", "Tool latency", ["tool"], registry=self.registry
        )
        self.inflight = Gauge("hmt_mcp_inflight", "Executing tools", registry=self.registry)

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        handler: Callable[[str, dict[str, Any]], CallToolResult] = dispatch,
    ) -> CallToolResult:
        tool = name if name in TOOLS else "unknown"
        start, status = perf_counter(), "exception"
        self.inflight.inc()
        try:
            result = handler(name, arguments)
            status = "error" if result.isError else "success"
            return result
        except Exception:
            return error_result("INTERNAL_ERROR")
        finally:
            self.calls.labels(tool, status).inc()
            self.latency.labels(tool).observe(perf_counter() - start)
            self.inflight.dec()
