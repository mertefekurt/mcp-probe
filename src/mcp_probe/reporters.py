"""Human-readable and machine-readable report generation."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import asdict
from pathlib import Path

from mcp_probe.models import RunResult


def terminal_report(run: RunResult, color: bool = True) -> str:
    """Render a compact terminal report."""
    green = "\033[32m" if color else ""
    red = "\033[31m" if color else ""
    dim = "\033[2m" if color else ""
    reset = "\033[0m" if color else ""
    lines = [
        f"mcp-probe · {run.scenario}",
        f"{dim}server: {run.server_name} {run.server_version}{reset}",
        "",
    ]
    for result in run.results:
        marker = f"{green}PASS{reset}" if result.passed else f"{red}FAIL{reset}"
        lines.append(f"{marker}  {result.name}  {dim}{result.latency_ms:.1f}ms{reset}")
        lines.extend(f"      {red}{failure}{reset}" for failure in result.failures)
    lines.extend(
        [
            "",
            f"{run.passed} passed, {run.failed} failed, {len(run.results)} total",
        ]
    )
    return "\n".join(lines)


def write_json(run: RunResult, path: Path) -> None:
    """Write a complete JSON report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(run), indent=2) + "\n", encoding="utf-8")


def write_junit(run: RunResult, path: Path) -> None:
    """Write a JUnit XML report suitable for CI test annotations."""
    suite = ET.Element(
        "testsuite",
        {
            "name": run.scenario,
            "tests": str(len(run.results)),
            "failures": str(run.failed),
            "time": f"{sum(result.latency_ms for result in run.results) / 1000:.6f}",
        },
    )
    for result in run.results:
        case = ET.SubElement(
            suite,
            "testcase",
            {
                "name": result.name,
                "classname": f"mcp.{result.tool}",
                "time": f"{result.latency_ms / 1000:.6f}",
            },
        )
        if not result.passed:
            failure = ET.SubElement(case, "failure", {"message": result.failures[0]})
            failure.text = "\n".join(result.failures)
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(suite).write(path, encoding="unicode", xml_declaration=True)
