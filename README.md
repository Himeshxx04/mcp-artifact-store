# MCP Artifact Store

> Shared artifact store for multi-agent systems — reduces context window bloat by storing large tool outputs and passing only artifact IDs between agents.

---

## The Problem

In multi-agent pipelines, agents pass large payloads through shared graph state:

```
Agent A  ──────────────────────────────────────────────►  Agent B
         "Here is the full 15KB analysis: {...full JSON...}"
```

As pipelines grow, this bloats context windows, increases token costs, and creates hard limits on what agents can pass to each other.

## The Solution

Store the payload once. Pass only a short artifact ID:

```
Agent A  ──────────────────────────────────────────────►  Agent B
              "artifact_id: art_8e565a6d"  (12 bytes)
```

Agent B fetches the full payload from the store only when it needs it. Context stays clean.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     MCP Artifact Store                        │
├─────────────────────────┬────────────────────────────────────┤
│   React Dashboard       │   LangGraph / Claude Agents        │
│   (port 5173)           │   (any MCP client)                 │
│         │               │          │                         │
│    HTTP fetch()         │   MCP over stdio                   │
│         │               │          │                         │
│         ▼               │          ▼                         │
│   FastAPI (port 8000)   │    FastMCP Server                  │
│         │               │          │                         │
│         └───────────────┴──────────┘                         │
│                         │                                     │
│                   SQLAlchemy ORM                              │
│                         │                                     │
│              PostgreSQL in Docker (:5432)                     │
│              ┌───────────┴───────────┐                        │
│           artifacts             audit_log                     │
└──────────────────────────────────────────────────────────────┘
```

**Two interfaces, one store:**
- **FastAPI** — HTTP endpoints consumed by the React dashboard
- **FastMCP** — MCP tools consumed by LangGraph agents or Claude Desktop

Both call the same `backend/services/storage.py` functions.

---

## Features

- **Write artifacts** with TTL, ownership, and per-reader access control
- **Read artifacts** by ID — access checked against `allowed_readers`
- **List artifacts** — only shows what the requesting agent is allowed to see
- **Delete artifacts** — only the original creator can delete
- **Audit log** — every READ, WRITE, LIST, DELETE is logged atomically
- **React dashboard** — live health indicator, context-saved metric, formatted JSON viewer
- **TTL enforcement** — expired artifacts are invisible to all operations

---

## Demo — Codebase Auditor Pipeline

A two-agent LangGraph pipeline that audits a Python codebase:

```
[Analyzer Agent]
  1. Reads .py files from a directory
  2. Sends code to GPT-4o-mini for analysis
  3. Writes findings JSON to artifact store  →  receives artifact_id
                    ↓  only artifact_id travels in graph state
[Reporter Agent]
  4. Reads findings using artifact_id
  5. Generates a structured markdown audit report
```

**Without artifact store:** full findings blob (~1.6 KB) travels between agents  
**With artifact store:** 12-byte artifact_id travels between agents

### Run the demo

```bash
# Audit the backend directory
python -m examples.codebase_auditor.main backend

# Audit any directory
python -m examples.codebase_auditor.main path/to/your/code
```

**Sample output:**

```
[Analyzer] Found 12 file(s)
[Analyzer] Analysis complete — findings payload: 1780 bytes
[Analyzer] ✅ Stored as artifact: art_8e565a6d
[Analyzer] → Handing off artifact_id only — 1780 bytes stay in the store

[Reporter] Received artifact_id: art_8e565a6d
[Reporter] ✅ Fetched artifact — 1780 bytes, 3 finding(s)
[Reporter] ✅ Report generated

Artifact ID : art_8e565a6d  ← stored, any authorized agent can read this
```

---

## Project Structure

```
mcp-artifact-store/
├── main.py                        ← FastAPI entry point
├── backend/
│   ├── models/                    ← SQLAlchemy models (Artifact, AuditLog)
│   ├── routes/artifacts.py        ← HTTP endpoints
│   ├── schemas/artifacts.py       ← Pydantic request/response schemas
│   ├── services/storage.py        ← Core business logic
│   └── db/session.py              ← DB connection
├── server/
│   ├── mcp_server.py              ← FastMCP entry point
│   └── tools/artifacts.py         ← MCP tool definitions
├── examples/
│   └── codebase_auditor/          ← LangGraph demo pipeline
│       ├── main.py                ← StateGraph orchestrator
│       ├── agents/analyzer.py     ← Agent 1: analyze + write artifact
│       └── agents/reporter.py     ← Agent 2: read artifact + generate report
├── dashboard/                     ← React + Vite + Tailwind frontend
├── alembic/                       ← DB migrations
└── requirements.txt
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Docker Desktop
- Node.js 18+
- OpenAI API key

### 1. Clone and install

```bash
git clone https://github.com/Himeshxx04/mcp-artifact-store.git
cd mcp-artifact-store

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://postgres:password@127.0.0.1:5432/artifact_store
OPENAI_API_KEY=your-openai-api-key-here
ALLOWED_ORIGINS=http://localhost:5173
```

### 3. Start the database

```bash
docker run --name artifact-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=artifact_store \
  -p 5432:5432 -d postgres
```

### 4. Run migrations

```bash
alembic upgrade head
```

### 5. Start the FastAPI server

```bash
uvicorn main:app --reload
# API docs → http://127.0.0.1:8000/docs
```

### 6. Start the dashboard

```bash
cd dashboard
npm install
npm run dev
# Dashboard → http://localhost:5173
```

### 7. Run the demo

```bash
python -m examples.codebase_auditor.main backend
```

---

## MCP Tools

Connect any MCP-compatible client to `server/mcp_server.py`:

| Tool | Description |
|------|-------------|
| `write_artifact_tool` | Store data, get back an artifact_id |
| `read_artifact_tool` | Fetch data by artifact_id (access controlled) |
| `list_artifacts_tool` | List all artifacts visible to the requester |
| `delete_artifact_tool` | Delete an artifact (creator only) |

**Claude Desktop config:**

```json
{
  "mcpServers": {
    "artifact-store": {
      "command": "python",
      "args": ["-m", "server.mcp_server"],
      "cwd": "/path/to/mcp-artifact-store"
    }
  }
}
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check (includes DB connectivity) |
| `POST` | `/artifacts/` | Write a new artifact |
| `GET` | `/artifacts/` | List artifacts for a requester |
| `GET` | `/artifacts/{id}` | Read a specific artifact |
| `DELETE` | `/artifacts/{id}` | Delete an artifact |

Full interactive docs: `http://127.0.0.1:8000/docs`

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI |
| MCP Server | FastMCP |
| Database | PostgreSQL (Docker) |
| ORM + Migrations | SQLAlchemy + Alembic |
| Agent Framework | LangGraph |
| LLM | OpenAI GPT-4o-mini |
| Dashboard | React + Vite + Tailwind CSS |

---

## Roadmap

- [ ] API key authentication for remote deployment
- [ ] S3/R2 backend for large artifact storage
- [ ] Deploy to Railway/Render as a hosted service
- [ ] Python SDK (`pip install mcp-artifact-store`)
- [ ] Prebuilt LangGraph node factory for one-line integration

---

## Built by

Himesh Pandey — Final year ECE, PES University Bangalore  
[GitHub](https://github.com/Himeshxx04)

---

*Open source. Built to learn, built to ship.*
