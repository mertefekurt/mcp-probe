"""Minimal newline-delimited JSON-RPC client for stdio MCP servers."""

from __future__ import annotations

import json
import os
import queue
import subprocess
import threading
from collections.abc import Iterator
from typing import Any, TextIO

from mcp_probe.errors import ProtocolError
from mcp_probe.models import ServerConfig


def _read_lines(stream: TextIO, output: queue.Queue[str | None]) -> None:
    try:
        for line in stream:
            output.put(line)
    finally:
        output.put(None)


class StdioClient:
    """Manage one MCP server process and correlate JSON-RPC responses."""

    def __init__(self, config: ServerConfig) -> None:
        self._config = config
        self._process: subprocess.Popen[str] | None = None
        self._stdout: queue.Queue[str | None] = queue.Queue()
        self._stderr_lines: list[str] = []
        self._next_id = 1

    def __enter__(self) -> StdioClient:
        env = os.environ.copy()
        env.update(self._config.env)
        try:
            self._process = subprocess.Popen(
                self._config.command,
                cwd=self._config.cwd,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                bufsize=1,
            )
        except OSError as error:
            raise ProtocolError(f"could not start server: {error}") from error

        assert self._process.stdout is not None
        assert self._process.stderr is not None
        threading.Thread(
            target=_read_lines, args=(self._process.stdout, self._stdout), daemon=True
        ).start()
        threading.Thread(target=self._capture_stderr, daemon=True).start()
        return self

    def _capture_stderr(self) -> None:
        assert self._process is not None
        assert self._process.stderr is not None
        self._stderr_lines.extend(line.rstrip() for line in self._process.stderr)

    def __exit__(self, *_: object) -> None:
        if self._process is None:
            return
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=2)

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        message: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        self._write(message)

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        message: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            message["params"] = params
        self._write(message)

        while True:
            raw = self._read()
            try:
                response = json.loads(raw)
            except json.JSONDecodeError as error:
                raise ProtocolError(f"server emitted invalid JSON: {raw.rstrip()}") from error
            if not isinstance(response, dict):
                raise ProtocolError("server response must be a JSON object")
            if response.get("id") != request_id:
                continue
            if "error" in response:
                error = response["error"]
                raise ProtocolError(f"{method} failed: {error}")
            result = response.get("result")
            if not isinstance(result, dict):
                raise ProtocolError(f"{method} returned a non-object result")
            return result

    def _write(self, message: dict[str, Any]) -> None:
        if self._process is None or self._process.stdin is None:
            raise ProtocolError("server process is not running")
        if self._process.poll() is not None:
            raise ProtocolError(self._exit_message())
        try:
            self._process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
            self._process.stdin.flush()
        except BrokenPipeError as error:
            raise ProtocolError(self._exit_message()) from error

    def _read(self) -> str:
        try:
            line = self._stdout.get(timeout=self._config.timeout_seconds)
        except queue.Empty as error:
            raise ProtocolError(
                f"server did not respond within {self._config.timeout_seconds:g}s"
            ) from error
        if line is None:
            raise ProtocolError(self._exit_message())
        return line

    def _exit_message(self) -> str:
        code = self._process.poll() if self._process is not None else "unknown"
        suffix = f"; stderr: {' | '.join(self._stderr_lines[-3:])}" if self._stderr_lines else ""
        return f"server exited unexpectedly with code {code}{suffix}"

    def initialize(self) -> dict[str, Any]:
        result = self.request(
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "mcp-probe", "version": "0.1.0"},
            },
        )
        self.notify("notifications/initialized")
        return result

    def list_tools(self) -> Iterator[dict[str, Any]]:
        cursor: str | None = None
        while True:
            params = {"cursor": cursor} if cursor else None
            result = self.request("tools/list", params)
            tools = result.get("tools")
            if not isinstance(tools, list):
                raise ProtocolError("tools/list result is missing a tools array")
            for tool in tools:
                if not isinstance(tool, dict):
                    raise ProtocolError("tools/list contains a non-object tool")
                yield tool
            cursor_value = result.get("nextCursor")
            if not isinstance(cursor_value, str) or not cursor_value:
                return
            cursor = cursor_value
