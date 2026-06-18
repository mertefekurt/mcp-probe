from mcp_probe.assertions import evaluate, resolve_path
from mcp_probe.models import Check


def test_resolve_path_handles_objects_and_arrays() -> None:
    response = {"content": [{"text": "hello"}]}

    assert resolve_path(response, "content.0.text") == "hello"


def test_equals_reports_a_useful_difference() -> None:
    failure = evaluate(Check("value", "equals", 7), {"value": 8})

    assert failure == "value: expected 7, got 8"


def test_contains_supports_strings_and_lists() -> None:
    assert evaluate(Check("text", "contains", "agent"), {"text": "agent tooling"}) is None
    assert evaluate(Check("items", "contains", "mcp"), {"items": ["mcp", "cli"]}) is None


def test_matches_uses_regular_expressions() -> None:
    assert evaluate(Check("slug", "matches", r"^[a-z-]+$"), {"slug": "mcp-probe"}) is None


def test_exists_can_assert_absence() -> None:
    assert evaluate(Check("error", "exists", False), {"result": "ok"}) is None


def test_missing_path_and_failed_pattern_are_reported() -> None:
    missing = evaluate(Check("missing.value", "equals", 1), {"value": 1})
    mismatch = evaluate(Check("slug", "matches", r"^\d+$"), {"slug": "mcp-probe"})

    assert missing == "missing.value: path does not exist"
    assert "to match" in mismatch
