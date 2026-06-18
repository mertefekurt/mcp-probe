"""Response path lookup and assertion evaluation."""

from __future__ import annotations

import re
from typing import Any

from mcp_probe.models import Check

_MISSING = object()


def resolve_path(value: Any, path: str) -> Any:
    """Resolve dot-separated object keys and list indexes."""
    current = value
    for segment in path.split("."):
        if isinstance(current, dict) and segment in current:
            current = current[segment]
        elif isinstance(current, list) and segment.isdigit() and int(segment) < len(current):
            current = current[int(segment)]
        else:
            return _MISSING
    return current


def evaluate(check: Check, response: dict[str, Any]) -> str | None:
    """Return a human-readable failure or None when a check passes."""
    actual = resolve_path(response, check.path)
    if check.operator == "exists":
        expected_exists = True if check.expected is None else bool(check.expected)
        exists = actual is not _MISSING
        if exists == expected_exists:
            return None
        return f"{check.path}: expected exists={expected_exists}, got exists={exists}"

    if actual is _MISSING:
        return f"{check.path}: path does not exist"
    if check.operator == "equals":
        if actual == check.expected:
            return None
        return f"{check.path}: expected {check.expected!r}, got {actual!r}"
    if check.operator == "contains":
        if isinstance(actual, (str, list, dict)) and check.expected in actual:
            return None
        return f"{check.path}: expected value to contain {check.expected!r}, got {actual!r}"
    if check.operator == "matches":
        if isinstance(actual, str) and re.search(str(check.expected), actual):
            return None
        return f"{check.path}: expected {actual!r} to match {check.expected!r}"
    return f"{check.path}: unsupported operator {check.operator!r}"
