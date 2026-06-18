import json
import xml.etree.ElementTree as ET
from pathlib import Path

from mcp_probe.models import RunResult
from mcp_probe.models import TestResult as ProbeTestResult
from mcp_probe.reporters import terminal_report, write_json, write_junit


def sample_run() -> RunResult:
    return RunResult(
        scenario="contracts",
        server_name="sample",
        server_version="1.2.3",
        results=(
            ProbeTestResult("passes", "echo", True, 4.2),
            ProbeTestResult("fails", "search", False, 8.5, ("unexpected result",)),
        ),
    )


def test_terminal_report_summarizes_results_without_color() -> None:
    report = terminal_report(sample_run(), color=False)

    assert "1 passed, 1 failed, 2 total" in report
    assert "\033[" not in report


def test_json_report_is_machine_readable(tmp_path: Path) -> None:
    path = tmp_path / "report.json"

    write_json(sample_run(), path)

    assert json.loads(path.read_text())["results"][1]["failures"] == ["unexpected result"]


def test_junit_report_contains_failure(tmp_path: Path) -> None:
    path = tmp_path / "report.xml"

    write_junit(sample_run(), path)
    root = ET.parse(path).getroot()

    assert root.attrib["failures"] == "1"
    cases = root.findall("./testcase")
    assert cases[0].find("failure") is None
    assert cases[1].find("failure") is not None
