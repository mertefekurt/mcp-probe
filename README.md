# MCP Probe

Contract testing for stdio MCP servers. In practice it is a narrow guardrail for model evaluation, traces, retrieval, and prompt review: one command, a concrete report, and very little ceremony.

![MCP Probe cover](assets/readme-cover.svg)

## Where it fits

- for model evaluation, traces, retrieval, and prompt review
- quick local checks without a service dependency
- review notes that should stay easy to reproduce

## Run it

```bash
git clone https://github.com/mertefekurt/mcp-probe.git
cd mcp-probe
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
mcp-probe examples/demo.json
```

## Project map

```text
.github/        CI workflow
examples/       sample inputs
src/            package source
tests/          test coverage
.gitignore      project file
pyproject.toml  package metadata
```
