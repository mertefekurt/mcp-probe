"""Scenario execution against an MCP server."""

from __future__ import annotations

import time
from typing import Any

import jsonschema

from mcp_probe.assertions import evaluate
from mcp_probe.errors import ProtocolError
from mcp_probe.models import RunResult, Scenario, TestResult
from mcp_probe.protocol import StdioClient


def _tool_map(tools: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for tool in tools:
        name = tool.get("name")
        if not isinstance(name, str) or not name:
            raise ProtocolError("tools/list returned a tool without a valid name")
        if name in mapped:
            raise ProtocolError(f"tools/list returned duplicate tool name: {name}")
        mapped[name] = tool
    return mapped


def run_scenario(scenario: Scenario) -> RunResult:
    """Execute every test while keeping a single initialized server process."""
    with StdioClient(scenario.server) as client:
        initialized = client.initialize()
        server_info = initialized.get("serverInfo", {})
        if not isinstance(server_info, dict):
            server_info = {}
        server_name = str(server_info.get("name", "unknown"))
        server_version = str(server_info.get("version", "unknown"))
        tools = _tool_map(list(client.list_tools()))
        results: list[TestResult] = []

        for test in scenario.tests:
            failures: list[str] = []
            tool = tools.get(test.tool)
            if tool is None:
                failures.append(f"tool is not advertised by server: {test.tool}")
                results.append(
                    TestResult(
                        name=test.name,
                        tool=test.tool,
                        passed=False,
                        latency_ms=0,
                        failures=tuple(failures),
                    )
                )
                continue

            schema = tool.get("inputSchema", {})
            if not isinstance(schema, dict):
                failures.append("tool inputSchema is not an object")
            else:
                try:
                    jsonschema.validate(test.arguments, schema)
                except jsonschema.ValidationError as error:
                    failures.append(f"arguments violate inputSchema: {error.message}")

            response: dict[str, Any] | None = None
            started = time.perf_counter()
            if not failures:
                try:
                    response = client.request(
                        "tools/call", {"name": test.tool, "arguments": test.arguments}
                    )
                except ProtocolError as error:
                    failures.append(str(error))
            latency_ms = (time.perf_counter() - started) * 1000

            if test.max_latency_ms is not None and latency_ms > test.max_latency_ms:
                failures.append(
                    f"latency {latency_ms:.1f}ms exceeded limit {test.max_latency_ms:.1f}ms"
                )
            if response is not None:
                failures.extend(
                    failure
                    for check in test.checks
                    if (failure := evaluate(check, response)) is not None
                )
                if response.get("isError") is True:
                    failures.append("tool returned isError=true")

            results.append(
                TestResult(
                    name=test.name,
                    tool=test.tool,
                    passed=not failures,
                    latency_ms=latency_ms,
                    failures=tuple(failures),
                    response=response,
                )
            )

    return RunResult(
        scenario=scenario.name,
        server_name=server_name,
        server_version=server_version,
        results=tuple(results),
    )
