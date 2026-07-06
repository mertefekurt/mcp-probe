<p align="center">
  <img src="assets/readme-cover.svg" alt="MCP Probe cover" width="100%" />
</p>

# MCP Probe

![stack](https://img.shields.io/badge/stack-Python-be185d?style=flat-square) ![python](https://img.shields.io/badge/python-3.11-4b5563?style=flat-square) ![license](https://img.shields.io/badge/license-MIT-2563eb?style=flat-square) ![ci](https://img.shields.io/badge/ci-GitHub%20Actions-16a34a?style=flat-square)

Contract testing for stdio MCP servers.

## Good for

- quick local checks around developer tooling
- small CI jobs where a readable report is enough
- review workflows that need deterministic output
- examples based on `examples/demo.json`

## Run it

```bash
python -m pip install -e ".[dev]"
mcp-probe examples/demo.json
```

## Project notes

- Command: `mcp-probe`
- Language: Python
- Python: `>=3.11`
- Tests: `pytest`

## Layout

```text
.github/        CI workflow
examples/       sample inputs
src/            package source
tests/          test coverage
.gitignore      project file
pyproject.toml  package metadata
```

## Check locally

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest
python -m mcp_probe --help
```
