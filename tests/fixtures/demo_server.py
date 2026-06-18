"""Tiny MCP server used by tests and the example scenario."""

from __future__ import annotations

import json
import sys
from typing import Any


def respond(request_id: int, result: dict[str, Any]) -> None:
    print(json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}), flush=True)


for line in sys.stdin:
    message = json.loads(line)
    if "id" not in message:
        continue
    request_id = message["id"]
    method = message["method"]
    if method == "initialize":
        respond(
            request_id,
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "demo-server", "version": "1.0.0"},
            },
        )
    elif method == "tools/list":
        respond(
            request_id,
            {
                "tools": [
                    {
                        "name": "slugify",
                        "description": "Convert text into a URL-safe slug.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"text": {"type": "string", "minLength": 1}},
                            "required": ["text"],
                            "additionalProperties": False,
                        },
                    }
                ]
            },
        )
    elif method == "tools/call":
        text = message["params"]["arguments"]["text"]
        slug = "-".join(text.lower().split())
        respond(
            request_id,
            {"content": [{"type": "text", "text": slug}], "structuredContent": {"slug": slug}},
        )
