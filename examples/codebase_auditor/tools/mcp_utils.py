"""
MCP tool response parser.

langchain-mcp-adapters 0.1.0 returns tool results as a list of content
block dicts rather than the raw dict the tool returned. Observed shape:

    [{'type': 'text', 'text': '{"artifact_id": "art_abc123", ...}', 'id': '...'}]

This utility unwraps that structure so agents work with plain Python dicts.
"""

import json
from typing import Any


def parse_tool_result(result: Any) -> dict:
    """
    Unwrap an MCP tool response into a plain dict.

    Handles all observed shapes:
      - list of content block dicts  → JSON-parse the 'text' field
      - content block dict           → JSON-parse the 'text' field
      - object with .text attribute  → JSON-parse .text
      - plain JSON string            → JSON-parse directly
      - plain dict (no 'type' key)   → returned as-is

    Raises:
        ValueError: if the result cannot be parsed into a dict.
    """
    # Unwrap list — take first content block
    if isinstance(result, list):
        if not result:
            raise ValueError("MCP tool returned an empty list")
        result = result[0]

    # Content block dict: {'type': 'text', 'text': '{...json...}', 'id': '...'}
    if isinstance(result, dict) and "type" in result and "text" in result:
        return json.loads(result["text"])

    # Plain dict with no content-block wrapper — return as-is
    if isinstance(result, dict):
        return result

    # Object with a .text attribute (e.g. TextContent dataclass)
    if hasattr(result, "text"):
        return json.loads(result.text)

    # Plain JSON string
    if isinstance(result, str):
        return json.loads(result)

    raise ValueError(
        f"Cannot parse MCP tool result — unexpected type: {type(result)!r}\n"
        f"Value: {result!r}"
    )
