import sys
from pathlib import Path

from mcp_probe.models import Check, Scenario, ServerConfig
from mcp_probe.models import TestCase as ProbeTestCase
from mcp_probe.runner import run_scenario

FIXTURE = Path(__file__).parent / "fixtures" / "demo_server.py"


def scenario_for(test: ProbeTestCase) -> Scenario:
    return Scenario(
        name="integration",
        server=ServerConfig(command=(sys.executable, str(FIXTURE)), timeout_seconds=2),
        tests=(test,),
    )


def test_runner_executes_tool_and_checks_response() -> None:
    scenario = scenario_for(
        ProbeTestCase(
            name="slug",
            tool="slugify",
            arguments={"text": "MCP Contract Test"},
            checks=(Check("structuredContent.slug", "equals", "mcp-contract-test"),),
            max_latency_ms=500,
        )
    )

    result = run_scenario(scenario)

    assert result.passed == 1
    assert result.server_name == "demo-server"


def test_runner_reports_missing_tool_without_crashing() -> None:
    scenario = scenario_for(ProbeTestCase(name="missing", tool="unknown", arguments={}, checks=()))

    result = run_scenario(scenario)

    assert result.failed == 1
    assert "not advertised" in result.results[0].failures[0]


def test_runner_validates_arguments_before_calling_tool() -> None:
    scenario = scenario_for(ProbeTestCase(name="invalid", tool="slugify", arguments={}, checks=()))

    result = run_scenario(scenario)

    assert result.failed == 1
    assert "inputSchema" in result.results[0].failures[0]
