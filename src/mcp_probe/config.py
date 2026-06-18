"""Scenario loading and validation."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from mcp_probe.errors import ConfigurationError
from mcp_probe.models import Check, Scenario, ServerConfig, TestCase

_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_OPERATORS = {"equals", "contains", "matches", "exists"}


def _required(value: dict[str, Any], key: str, context: str) -> Any:
    if key not in value:
        raise ConfigurationError(f"{context} is missing required field '{key}'")
    return value[key]


def _expand_env(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in os.environ:
            raise ConfigurationError(f"environment variable '{name}' is not set")
        return os.environ[name]

    return _ENV_PATTERN.sub(replace, value)


def _load_check(raw: Any, context: str) -> Check:
    if not isinstance(raw, dict):
        raise ConfigurationError(f"{context} must be an object")
    path = _required(raw, "path", context)
    operator = _required(raw, "operator", context)
    if not isinstance(path, str) or not path:
        raise ConfigurationError(f"{context}.path must be a non-empty string")
    if operator not in _OPERATORS:
        allowed = ", ".join(sorted(_OPERATORS))
        raise ConfigurationError(f"{context}.operator must be one of: {allowed}")
    if operator != "exists" and "expected" not in raw:
        raise ConfigurationError(f"{context} requires an 'expected' value")
    return Check(path=path, operator=operator, expected=raw.get("expected"))


def load_scenario(path: Path) -> Scenario:
    """Load a JSON scenario and resolve environment placeholders."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ConfigurationError(f"scenario file not found: {path}") from error
    except json.JSONDecodeError as error:
        raise ConfigurationError(
            f"invalid JSON at line {error.lineno}, column {error.colno}: {error.msg}"
        ) from error

    if not isinstance(raw, dict):
        raise ConfigurationError("scenario root must be an object")

    name = _required(raw, "name", "scenario")
    server_raw = _required(raw, "server", "scenario")
    tests_raw = _required(raw, "tests", "scenario")
    if not isinstance(name, str) or not name:
        raise ConfigurationError("scenario.name must be a non-empty string")
    if not isinstance(server_raw, dict):
        raise ConfigurationError("scenario.server must be an object")

    command = _required(server_raw, "command", "scenario.server")
    if not isinstance(command, list) or not command or not all(isinstance(x, str) for x in command):
        raise ConfigurationError("scenario.server.command must be a non-empty string array")

    env_raw = server_raw.get("env", {})
    if not isinstance(env_raw, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in env_raw.items()
    ):
        raise ConfigurationError("scenario.server.env must map strings to strings")
    env = {key: _expand_env(value) for key, value in env_raw.items()}

    cwd_raw = server_raw.get("cwd")
    cwd = (path.parent / cwd_raw).resolve() if isinstance(cwd_raw, str) else None
    timeout = server_raw.get("timeout_seconds", 10.0)
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ConfigurationError("scenario.server.timeout_seconds must be positive")

    if not isinstance(tests_raw, list) or not tests_raw:
        raise ConfigurationError("scenario.tests must be a non-empty array")

    tests: list[TestCase] = []
    seen_names: set[str] = set()
    for index, test_raw in enumerate(tests_raw):
        context = f"scenario.tests[{index}]"
        if not isinstance(test_raw, dict):
            raise ConfigurationError(f"{context} must be an object")
        test_name = _required(test_raw, "name", context)
        tool = _required(test_raw, "tool", context)
        arguments = test_raw.get("arguments", {})
        checks_raw = test_raw.get("checks", [])
        if not isinstance(test_name, str) or not test_name:
            raise ConfigurationError(f"{context}.name must be a non-empty string")
        if test_name in seen_names:
            raise ConfigurationError(f"duplicate test name: {test_name}")
        seen_names.add(test_name)
        if not isinstance(tool, str) or not tool:
            raise ConfigurationError(f"{context}.tool must be a non-empty string")
        if not isinstance(arguments, dict):
            raise ConfigurationError(f"{context}.arguments must be an object")
        if not isinstance(checks_raw, list):
            raise ConfigurationError(f"{context}.checks must be an array")
        checks = tuple(
            _load_check(check, f"{context}.checks[{check_index}]")
            for check_index, check in enumerate(checks_raw)
        )
        max_latency = test_raw.get("max_latency_ms")
        if max_latency is not None and (
            not isinstance(max_latency, (int, float)) or max_latency <= 0
        ):
            raise ConfigurationError(f"{context}.max_latency_ms must be positive")
        tests.append(
            TestCase(
                name=test_name,
                tool=tool,
                arguments=arguments,
                checks=checks,
                max_latency_ms=float(max_latency) if max_latency is not None else None,
            )
        )

    server = ServerConfig(
        command=tuple(command),
        env=env,
        cwd=cwd,
        timeout_seconds=float(timeout),
    )
    return Scenario(name=name, server=server, tests=tuple(tests))
