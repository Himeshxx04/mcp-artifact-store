"""
Codebase Auditor — V1 Demo
--------------------------
A two-agent LangGraph pipeline that demonstrates the MCP Artifact Store.

Flow:
    [Analyzer Agent]
        1. Reads .py files from a directory
        2. Sends code to LLM for analysis
        3. Writes findings JSON to artifact store  →  gets artifact_id back
                        ↓ (only artifact_id travels through graph state)
    [Reporter Agent]
        4. Reads findings from artifact store using artifact_id
        5. Generates a structured markdown audit report

Without the artifact store:
    Full findings blob (~5-20KB) would travel through graph state between agents.

With the artifact store:
    Only a short artifact_id string (e.g. "art_3f9bc1a2") travels between agents.

Usage:
    python -m examples.codebase_auditor.main                     # audits ./backend by default
    python -m examples.codebase_auditor.main <path/to/directory> # audits any directory
"""

import asyncio
import sys
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from langchain_mcp_adapters.client import MultiServerMCPClient

from examples.codebase_auditor.agents.analyzer import make_analyzer_node
from examples.codebase_auditor.agents.reporter import make_reporter_node

load_dotenv()

# Project root — two levels up from examples/codebase_auditor/
PROJECT_ROOT = Path(__file__).parent.parent.parent


# ── Graph State ───────────────────────────────────────────────────────────────
# Intentionally minimal: only what needs to travel between nodes lives here.
# The full findings payload (KB of JSON) stays in the artifact store.

class CodebaseState(TypedDict):
    directory: str     # Input: path to the codebase to audit
    artifact_id: str   # Set by analyzer, consumed by reporter
    report: str        # Set by reporter, printed at the end


# ── Graph Builder ─────────────────────────────────────────────────────────────

def build_graph(write_tool, read_tool) -> object:
    """Wire up the two-node LangGraph pipeline."""
    graph = StateGraph(CodebaseState)

    graph.add_node("analyzer", make_analyzer_node(write_tool))
    graph.add_node("reporter", make_reporter_node(read_tool))

    graph.add_edge(START, "analyzer")
    graph.add_edge("analyzer", "reporter")
    graph.add_edge("reporter", END)

    return graph.compile()


# ── Entry Point ───────────────────────────────────────────────────────────────

async def run(directory: str) -> None:
    """
    Start the MCP server as a subprocess, connect to it,
    then run the two-agent pipeline.
    """
    # MCP server config — launches our FastMCP server via stdio transport.
    # The subprocess inherits the parent's environment (DATABASE_URL, OPENAI_API_KEY, etc.)
    server_config = {
        "artifact-store": {
            "command": sys.executable,            # same Python interpreter as venv
            "args": ["-m", "server.mcp_server"],  # runs server/mcp_server.py
            "transport": "stdio",
            "cwd": str(PROJECT_ROOT),             # so Python finds our modules
        }
    }

    print("\n" + "═" * 60)
    print("  MCP ARTIFACT STORE — Codebase Auditor Demo")
    print("═" * 60)
    print(f"  Target  : {directory}")
    print(f"  Store   : artifact store (PostgreSQL via Docker)")
    print("═" * 60)

    # langchain-mcp-adapters 0.1.0 removed context manager support.
    # Instantiate directly — client stays alive for the duration of this function,
    # keeping the MCP server subprocess running until run() returns.
    client = MultiServerMCPClient(server_config)
    tools = await client.get_tools()
    tool_map = {t.name: t for t in tools}

    # Verify the tools we need are available
    missing = [t for t in ("write_artifact_tool", "read_artifact_tool") if t not in tool_map]
    if missing:
        raise RuntimeError(
            f"Expected MCP tools not found: {missing}\n"
            f"Available tools: {list(tool_map.keys())}"
        )

    write_tool = tool_map["write_artifact_tool"]
    read_tool = tool_map["read_artifact_tool"]

    workflow = build_graph(write_tool, read_tool)

    result = await workflow.ainvoke({
        "directory": directory,
        "artifact_id": "",
        "report": "",
    })

    # ── Print final report ────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  AUDIT REPORT")
    print("═" * 60 + "\n")
    print(result["report"])
    print("\n" + "═" * 60)
    print(f"  Artifact ID : {result['artifact_id']}")
    print("  Findings are stored in the artifact store and can be")
    print("  read by any authorized agent using just the artifact_id.")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else str(PROJECT_ROOT / "backend")
    asyncio.run(run(target_dir))
