import json
from pathlib import Path

import pytest

from mcp_probe.config import load_scenario
from mcp_probe.errors import ConfigurationError


def write_scenario(path: Path, data: dict[str, object]) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def test_load_scenario_resolves_relative_cwd(tmp_path: Path) -> None:
    path = tmp_path / "scenario.json"
    write_scenario(
        path,
        {
            "name": "sample",
            "server": {"command": ["server"], "cwd": "runtime"},
            "tests": [{"name": "one", "tool": "echo"}],
        },
    )

    scenario = load_scenario(path)

    assert scenario.server.cwd == (tmp_path / "runtime").resolve()
    assert scenario.tests[0].arguments == {}


def test_load_scenario_expands_environment_variables(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MCP_TOKEN", "secret")
    path = tmp_path / "scenario.json"
    write_scenario(
        path,
        {
            "name": "sample",
            "server": {"command": ["server"], "env": {"TOKEN": "${MCP_TOKEN}"}},
            "tests": [{"name": "one", "tool": "echo"}],
        },
    )

    scenario = load_scenario(path)

    assert scenario.server.env == {"TOKEN": "secret"}


def test_load_scenario_rejects_duplicate_names(tmp_path: Path) -> None:
    path = tmp_path / "scenario.json"
    write_scenario(
        path,
        {
            "name": "sample",
            "server": {"command": ["server"]},
            "tests": [
                {"name": "duplicate", "tool": "a"},
                {"name": "duplicate", "tool": "b"},
            ],
        },
    )

    with pytest.raises(ConfigurationError, match="duplicate test name"):
        load_scenario(path)


def test_load_scenario_rejects_unknown_operator(tmp_path: Path) -> None:
    path = tmp_path / "scenario.json"
    write_scenario(
        path,
        {
            "name": "sample",
            "server": {"command": ["server"]},
            "tests": [
                {
                    "name": "one",
                    "tool": "echo",
                    "checks": [{"path": "value", "operator": "approximately", "expected": 1}],
                }
            ],
        },
    )

    with pytest.raises(ConfigurationError, match="operator must be one of"):
        load_scenario(path)


def test_load_scenario_reports_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "scenario.json"
    path.write_text("{", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="invalid JSON"):
        load_scenario(path)


def test_load_scenario_rejects_unset_environment_variable(tmp_path: Path) -> None:
    path = tmp_path / "scenario.json"
    write_scenario(
        path,
        {
            "name": "sample",
            "server": {"command": ["server"], "env": {"TOKEN": "${UNSET_PROBE_TOKEN}"}},
            "tests": [{"name": "one", "tool": "echo"}],
        },
    )

    with pytest.raises(ConfigurationError, match="is not set"):
        load_scenario(path)


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ([], "root must be an object"),
        ({"name": "sample", "server": {"command": []}, "tests": []}, "command must"),
        (
            {"name": "sample", "server": {"command": ["server"]}, "tests": []},
            "non-empty array",
        ),
    ],
)
def test_load_scenario_rejects_invalid_shapes(tmp_path: Path, data: object, message: str) -> None:
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ConfigurationError, match=message):
        load_scenario(path)
