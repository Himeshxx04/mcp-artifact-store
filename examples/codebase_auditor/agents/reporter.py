"""
Reporter Agent
--------------
Receives an artifact_id from the analyzer, fetches the findings JSON
from the artifact store, then uses an LLM to produce a clean markdown
audit report.

Key point: this agent never sees the raw codebase — only the artifact_id
travels through the graph state between agents.
"""

import json
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from examples.codebase_auditor.tools.mcp_utils import parse_tool_result

REPORTER_ID = "codebase_reporter_agent"

_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def make_reporter_node(read_tool):
    """
    Factory that returns the reporter node function.
    Closes over read_tool so the node has access to the MCP tool
    without it needing to be in graph state.
    """

    async def reporter(state: dict) -> dict:
        artifact_id = state["artifact_id"]
        print(f"\n[Reporter] Received artifact_id: {artifact_id}")
        print("[Reporter] Fetching findings from artifact store...")

        # ── Step 1: Read findings from artifact store via MCP tool ────────
        raw = await read_tool.ainvoke({
            "artifact_id": artifact_id,
            "requester_id": REPORTER_ID,
        })

        findings_raw = parse_tool_result(raw)["data"]
        findings = json.loads(findings_raw)

        print(
            f"[Reporter] ✅ Fetched artifact — "
            f"{len(findings_raw.encode())} bytes, "
            f"{len(findings.get('findings', []))} finding(s)"
        )

        # ── Step 2: Build report generation prompt ────────────────────────
        prompt = f"""You are a senior engineering lead writing a codebase audit report.
Below are the raw audit findings as JSON. Convert them into a professional markdown report.

RAW FINDINGS:
{findings_raw}

Write the report with exactly these sections in this order:

# Codebase Audit Report

## Executive Summary
2-3 sentence overview of the codebase health.

## Findings

| File | Severity | Category | Issue | Suggestion |
|------|----------|----------|-------|------------|
(one row per finding, severity in CAPS)

## Strengths
- bullet list

## Top Priorities
1. First most important fix
2. Second
3. Third

## Conclusion
1-2 sentences on next steps.

Rules:
- Use proper markdown.
- Severity values: HIGH / MEDIUM / LOW / INFO
- Be direct and actionable — avoid filler language.
"""

        # ── Step 3: LLM generates the report ─────────────────────────────
        print("[Reporter] Generating audit report...")
        response = await _llm.ainvoke([HumanMessage(content=prompt)])
        report = response.content.strip()

        print(f"[Reporter] ✅ Report generated ({len(report)} chars)")

        return {"report": report}

    return reporter
