"""
Analyzer Agent
--------------
Reads Python files from a directory, sends them to an LLM for analysis,
then writes the findings JSON as an artifact in the store.

Returns only the artifact_id — the full findings blob never travels
through the graph state.
"""

import json
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from examples.codebase_auditor.tools.file_tools import read_python_files
from examples.codebase_auditor.tools.mcp_utils import parse_tool_result

# Agent identifiers — used for artifact ownership and access control
ANALYZER_ID = "codebase_auditor_agent"
REPORTER_ID = "codebase_reporter_agent"

# How long the artifact lives in the store (seconds)
ARTIFACT_TTL = 3600  # 1 hour

_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def make_analyzer_node(write_tool):
    """
    Factory that returns the analyzer node function.
    Closes over write_tool so the node has access to the MCP tool
    without it needing to be in graph state.
    """

    async def analyzer(state: dict) -> dict:
        directory = state["directory"]
        print(f"\n[Analyzer] Scanning directory: {directory}")

        # ── Step 1: Read all .py files from disk ─────────────────────────
        files = read_python_files(directory)
        if not files:
            raise ValueError(f"No Python files found in: {directory}")

        print(f"[Analyzer] Found {len(files)} file(s): {', '.join(files.keys())}")

        # ── Step 2: Build the analysis prompt ────────────────────────────
        code_sections = "\n\n".join(
            f"### {filename}\n```python\n{content}\n```"
            for filename, content in files.items()
        )

        prompt = f"""You are a senior software engineer performing a codebase audit.
Analyze the following Python files and return a JSON object with EXACTLY this structure:

{{
  "summary": "<2-3 sentence overall assessment>",
  "files_analyzed": <integer>,
  "findings": [
    {{
      "file": "<filename>",
      "severity": "<high|medium|low|info>",
      "category": "<bug|security|performance|style|design>",
      "issue": "<concise issue description>",
      "suggestion": "<concrete fix suggestion>"
    }}
  ],
  "strengths": ["<thing the codebase does well>"],
  "top_priorities": ["<most important fix>", "<second>", "<third>"]
}}

Rules:
- Return ONLY valid JSON. No markdown fences, no explanation outside the JSON.
- Every finding must have all 5 fields.
- top_priorities must contain exactly 3 items.

FILES TO ANALYZE:
{code_sections}
"""

        # ── Step 3: LLM analysis ─────────────────────────────────────────
        print("[Analyzer] Running LLM analysis...")
        response = await _llm.ainvoke([HumanMessage(content=prompt)])
        findings_raw = response.content.strip()

        # Strip accidental markdown fences the LLM sometimes adds
        if findings_raw.startswith("```"):
            findings_raw = findings_raw.split("```")[1]
            if findings_raw.startswith("json"):
                findings_raw = findings_raw[4:]
            findings_raw = findings_raw.strip()

        # Validate we got real JSON before storing it
        try:
            json.loads(findings_raw)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"LLM returned invalid JSON: {e}\n"
                f"First 300 chars: {findings_raw[:300]}"
            )

        payload_size = len(findings_raw.encode("utf-8"))
        print(f"[Analyzer] Analysis complete — findings payload: {payload_size} bytes")

        # ── Step 4: Write findings to artifact store via MCP tool ─────────
        print("[Analyzer] Writing findings to artifact store...")
        raw = await write_tool.ainvoke({
            "data": findings_raw,
            "created_by": ANALYZER_ID,
            "ttl_seconds": ARTIFACT_TTL,
            "allowed_readers": [ANALYZER_ID, REPORTER_ID],
        })

        artifact_id = parse_tool_result(raw)["artifact_id"]
        print(f"[Analyzer] ✅ Stored as artifact: {artifact_id}")
        print(
            f"[Analyzer] → Handing off artifact_id only — "
            f"{payload_size} bytes stay in the store, not in graph state"
        )

        return {"artifact_id": artifact_id}

    return analyzer
