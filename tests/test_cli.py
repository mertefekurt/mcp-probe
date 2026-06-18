import json
import sys
from pathlib import Path

from mcp_probe.cli import main

FIXTURE = Path(__file__).parent / "fixtures" / "demo_server.py"


def write_scenario(path: Path, expected: str) -> None:
    path.write_text(
        json.dumps(
            {
                "name": "CLI integration",
                "server": {"command": [sys.executable, str(FIXTURE)]},
                "tests": [
                    {
                        "name": "slug contract",
                        "tool": "slugify",
                        "arguments": {"text": "CLI Test"},
                        "checks": [
                            {
                                "path": "structuredContent.slug",
                                "operator": "equals",
                                "expected": expected,
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_cli_success_writes_reports(tmp_path: Path, capsys: object) -> None:
    scenario = tmp_path / "scenario.json"
    json_report = tmp_path / "report.json"
    junit_report = tmp_path / "report.xml"
    write_scenario(scenario, "cli-test")

    code = main(
        [
            str(scenario),
            "--no-color",
            "--json-report",
            str(json_report),
            "--junit-report",
            str(junit_report),
        ]
    )

    assert code == 0
    assert "1 passed, 0 failed" in capsys.readouterr().out  # type: ignore[attr-defined]
    assert json_report.exists()
    assert junit_report.exists()


def test_cli_returns_one_for_contract_failure(tmp_path: Path) -> None:
    scenario = tmp_path / "scenario.json"
    write_scenario(scenario, "wrong-value")

    assert main([str(scenario), "--no-color"]) == 1


def test_cli_returns_two_for_configuration_error(tmp_path: Path, capsys: object) -> None:
    code = main([str(tmp_path / "missing.json")])

    assert code == 2
    assert "scenario file not found" in capsys.readouterr().err  # type: ignore[attr-defined]
