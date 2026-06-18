"""Command-line entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mcp_probe import __version__
from mcp_probe.config import load_scenario
from mcp_probe.errors import ProbeError
from mcp_probe.reporters import terminal_report, write_json, write_junit
from mcp_probe.runner import run_scenario


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mcp-probe",
        description="Run contract tests against a stdio MCP server.",
    )
    parser.add_argument("scenario", type=Path, help="path to a JSON scenario")
    parser.add_argument("--json-report", type=Path, help="write a JSON report")
    parser.add_argument("--junit-report", type=Path, help="write a JUnit XML report")
    parser.add_argument("--no-color", action="store_true", help="disable ANSI colors")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        scenario = load_scenario(args.scenario.resolve())
        result = run_scenario(scenario)
    except ProbeError as error:
        print(f"mcp-probe: {error}", file=sys.stderr)
        return 2

    print(terminal_report(result, color=not args.no_color and sys.stdout.isatty()))
    if args.json_report:
        write_json(result, args.json_report)
    if args.junit_report:
        write_junit(result, args.junit_report)
    return 0 if result.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
