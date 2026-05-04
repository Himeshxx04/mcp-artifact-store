# MCP Artifact Store — Project Context

## What we are building
An open source MCP server that acts as a shared artifact store
for multi-agent systems. Reduces context window bloat by storing
large tool outputs and passing only artifact IDs between agents.

## My profile
- Name: Himesh Pandey, final year ECE, PES University Bangalore
- Stack: Python, FastAPI, LangChain, LangGraph, MCP, SQLAlchemy
- Goal: Learn while building, not blindly
- OS: Windows
- IDE: Antigravity (VS Code fork)

## Tech stack
- FastAPI — backend API
- FastMCP — MCP server
- PostgreSQL — storage (running via Docker)
- SQLAlchemy + Alembic — ORM and migrations
- LangGraph — demo agent
- React + Vite — dashboard
- Docker — deployment

## Environment setup
- venv activated at D:\mcp-artifact-store\venv
- Docker container name: artifact-db
- Start DB command: docker start artifact-db
- DATABASE_URL: postgresql://postgres:password@127.0.0.1:5432/artifact_store
- All dependencies installed via requirements.txt
- Local PostgreSQL must be STOPPED before running — conflicts with Docker on port 5432
- Stop local PG: Stop-Service -Name postgresql* -Force (run as Admin)
- Prevent auto-restart: Set-Service -Name postgresql* -StartupType Manual (run once, persists across reboots)
- If local PG keeps stealing port 5432: netstat -ano | findstr :5432 — two PIDs means conflict
- DEBUG=true in .env enables SQLAlchemy query logging (echo=True) — off by default

## Docker persistence rules
- docker stop / docker start → data safe ✅
- Docker Engine restart → data safe ✅
- docker rm artifact-db → data gone ❌ (never run this unless intentional)
- Container is persistent by default — no volume config needed for v1

## Startup checklist (every session)
1. Stop local PostgreSQL: Stop-Service -Name postgresql* (run as Admin)
2. Start Docker container: docker start artifact-db
3. Verify: docker ps (confirm artifact-db is Up and 0.0.0.0:5432->5432/tcp)
4. Then run code / alembic

## Project structure
mcp-artifact-store/
├── main.py                  ← FastAPI entry point
├── backend/
│   ├── models/
│   │   ├── base.py          ← Single Base = declarative_base()
│   │   ├── artifact.py      ← Artifact model
│   │   ├── audit_log.py     ← AuditLog model
│   │   └── __init__.py      ← imports both models
│   ├── routes/
│   │   └── artifacts.py     ← FastAPI endpoints
│   ├── schemas/
│   │   └── artifact.py      ← Pydantic request/response schemas
│   ├── services/
│   │   └── storage.py       ← Business logic (write, read, list, delete)
│   └── db/
│       └── session.py       ← DB connection + get_db()
├── server/
│   ├── mcp_server.py        ← FastMCP entry point
│   └── tools/
│       └── artifacts.py     ← MCP tool definitions
├── examples/
│   ├── codebase_auditor/    ← Demo: Agent 1 analyzes code, writes artifact; Agent 2 reads artifact, writes report
│   └── summarizer/          ← Demo Server B (future)
├── dashboard/               ← React frontend
├── alembic/                 ← DB migrations
│   └── versions/            ← Migration files live here
├── .env
├── requirements.txt
├── alembic.ini
└── README.md

## Files completed
- requirements.txt ✅
- .env ✅
- folder structure ✅
- backend/db/session.py ✅
- backend/models/base.py ✅
- backend/models/artifact.py ✅
- backend/models/audit_log.py ✅
- backend/models/__init__.py ✅
- alembic setup + env.py configured ✅
- First migration generated and applied ✅
- Second migration: audit_log artifact_id nullable=True ✅
- Tables created in PostgreSQL: artifacts, audit_log ✅
- backend/services/storage.py ✅ (write, read, list, delete)
- backend/schemas/artifact.py ✅
- backend/routes/artifacts.py ✅
- main.py ✅ (CORS, metadata, health check)
- All 4 endpoints tested via Swagger ✅
- server/tools/artifacts.py ✅
- server/mcp_server.py ✅

## Deployment fixes applied
- alembic/env.py: read DATABASE_URL env var to override alembic.ini hardcoded 127.0.0.1 URL
  — Render injects DATABASE_URL at build time; env.py was ignoring it, causing alembic upgrade head to fail
  — Fix: `db_url = os.getenv("DATABASE_URL"); if db_url: config.set_main_option("sqlalchemy.url", db_url)`
- render.yaml: added `plan: free` to both web services (was defaulting to paid $7/mo tier)
- render.yaml: added `&& alembic upgrade head` to buildCommand (Render shell requires paid plan)

## Bug fixes applied (post-initial-build)
- storage.py: write_artifact — artifact + audit log now commit in one atomic transaction (was two separate commits)
- storage.py: delete_artifact — artifact delete + audit log now commit in one atomic transaction (was two separate commits)
- storage.py: list_artifacts — allowed_readers filter moved from Python loop to SQL using CAST(allowed_readers AS JSONB) @> operator
- session.py: echo=True replaced with echo=DEBUG — SQL logging off by default, enabled via DEBUG=true in .env
- main.py: /health now runs SELECT 1 against DB — returns 200 if DB is up, 503 if DB is unreachable

## Completed
- examples/codebase_auditor/ — V1 demo: 2-agent LangGraph pipeline ✅ WORKING
  - main.py — StateGraph orchestrator, async, connects to MCP server via stdio
  - agents/analyzer.py — reads .py files, LLM analysis, writes artifact, returns artifact_id
  - agents/reporter.py — reads artifact by id, LLM generates markdown report
  - tools/file_tools.py — pure Python disk utility, walks directory, skips venv/__pycache__
  - tools/mcp_utils.py — parses langchain-mcp-adapters 0.1.0 response format (list of content block dicts)
  - Proven: 1519 bytes of findings stored as art_e2d246f2, only artifact_id traveled in graph state
  - Run: python -m examples.codebase_auditor.main [optional/path]

## Currently working on
- Full stack deployed and live ✅ — verify end-to-end, then LinkedIn post

## V1 Complete ✅ — Fully Deployed
All core features built, working, and live.

## Deployment architecture
- FastAPI backend    → Render web service (python main.py, binds $PORT)
- FastMCP server     → Render web service (python -m server.mcp_server, MCP_TRANSPORT=sse)
- PostgreSQL         → Render managed DB (free tier, 1GB)
- React dashboard    → Vercel (VITE_API_URL set to Render backend URL)
- render.yaml        → one-click deploy config at project root

## Live URLs
- Dashboard:   https://mcp-artifact-store.vercel.app
- Backend API: https://mcp-artifact-store-api.onrender.com
- API Docs:    https://mcp-artifact-store-api.onrender.com/docs
- MCP Server:  https://mcp-artifact-store-mcp.onrender.com/sse
- Health:      https://mcp-artifact-store-api.onrender.com/health

## Deployment env vars
Render (backend):
  DATABASE_URL   → auto-injected from Render managed DB
  ALLOWED_ORIGINS → https://your-app.vercel.app
  DEBUG          → false

Render (MCP server):
  DATABASE_URL   → auto-injected from Render managed DB
  MCP_TRANSPORT  → sse
  PORT           → auto-injected by Render

Vercel (dashboard):
  VITE_API_URL   → https://mcp-artifact-store-api.onrender.com

## Transport behaviour
- Local:  MCP_TRANSPORT not set → stdio (used by LangGraph demo)
- Remote: MCP_TRANSPORT=sse    → HTTP/SSE (deployable, anyone can connect)
- Remote MCP URL: https://mcp-artifact-store-mcp.onrender.com/sse

## Dashboard (React + Vite + Tailwind)
- Stack: React 19, Vite 8, Tailwind CSS v3
- Run: cd dashboard && npm run dev → http://localhost:5173
- Requires FastAPI running: uvicorn main:app --reload (port 8000)
- Components:
  - Header.jsx       — title + live health dot (polls /health every 30s)
  - StatsBar.jsx     — artifacts count, total stored, context saved (hero metric), expiring soon
  - ArtifactTable.jsx — sortable rows, click to inspect, delete button
  - DetailPanel.jsx  — formatted JSON viewer with per-artifact context saved callout
  - JsonViewer.jsx   — recursive syntax-highlighted JSON renderer (no external lib)
- Context saved metric: sum(size_bytes) - count * 12 (artifact_id is always 12 bytes)
- Requester ID input pre-filled with "codebase_auditor_agent" for demo

## Key design decisions
- UUID primary keys — security, not guessable
- allowed_readers as JSON column — list of server IDs that can read
- allowed_readers is set by the writing agent (hardcoded in V1 demo, should be orchestrator-defined in V2)
- V2 plan: pass allowed_readers through graph state from orchestrator so agents don't need to know pipeline topology
- created_at + expires_at timestamps — TTL enforcement
- size_bytes as Integer — dashboard metrics
- Data stored as TEXT in PostgreSQL (v1) — v2 will use S3
- Two separate Base instances bug fixed — single Base in base.py
- 127.0.0.1 instead of localhost — Windows IPv6 conflict fix
- Deployment model: v1 = local server only, no auth needed
- v2 = add API key auth for hosted/remote deployment
- Artifact-level access control via allowed_readers handles server isolation
- audit_log.artifact_id is nullable=True — LIST action logs use None since no single artifact is involved
- Only created_by can delete an artifact, not any allowed_reader
- HTTP status codes: 403 unauthorized, 410 expired, 404 not found
- Port conflict rule: local PostgreSQL steals 5432 from Docker — always stop it first
- CORS configured for React dashboard on localhost:5173
- allowed_readers JSON array filtered in SQL via CAST to JSONB + @> containment operator (not in Python)
- Audit log atomicity: WRITE and DELETE operations commit artifact change + audit log in one transaction

## Alembic commands to remember
# After changing any model:
alembic revision --autogenerate -m "describe what changed"
alembic upgrade head
# Always in this order — revision first, upgrade second

## Workflow rules
- Himesh writes every file skeleton first
- Two tries rule — Himesh attempts twice, then Claude provides solution
- Paste any Claude Code diff here before accepting
- Always follow startup checklist before coding