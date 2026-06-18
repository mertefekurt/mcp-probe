"""Typed models used by the scenario loader and runner."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ServerConfig:
    command: tuple[str, ...]
    env: dict[str, str] = field(default_factory=dict)
    cwd: Path | None = None
    timeout_seconds: float = 10.0


@dataclass(frozen=True)
class Check:
    path: str
    operator: str
    expected: Any = None


@dataclass(frozen=True)
class TestCase:
    name: str
    tool: str
    arguments: dict[str, Any]
    checks: tuple[Check, ...]
    max_latency_ms: float | None = None


@dataclass(frozen=True)
class Scenario:
    name: str
    server: ServerConfig
    tests: tuple[TestCase, ...]


@dataclass(frozen=True)
class TestResult:
    name: str
    tool: str
    passed: bool
    latency_ms: float
    failures: tuple[str, ...] = ()
    response: dict[str, Any] | None = None


@dataclass(frozen=True)
class RunResult:
    scenario: str
    server_name: str
    server_version: str
    results: tuple[TestResult, ...]

    @property
    def passed(self) -> int:
        return sum(result.passed for result in self.results)

    @property
    def failed(self) -> int:
        return len(self.results) - self.passed
