/**
 * App — root component.
 *
 * State:
 *   artifacts     — list from GET /artifacts/
 *   selectedArtifact — summary row the user clicked
 *   detail        — full artifact data from GET /artifacts/{id}
 *   health        — 'loading' | 'ok' | 'db_unavailable'
 *   requesterId   — agent ID used for all requests
 *   loading       — true while fetching artifact list
 *   detailLoading — true while fetching artifact detail
 *   deleting      — artifact_id currently being deleted (or null)
 *   error         — error message string or null
 */

import { useState, useEffect, useCallback } from "react"
import Header from "./components/Header"
import StatsBar from "./components/StatsBar"
import ArtifactTable from "./components/ArtifactTable"
import DetailPanel from "./components/DetailPanel"

const API = "http://127.0.0.1:8000"

function App() {
  const [artifacts, setArtifacts]               = useState([])
  const [selectedArtifact, setSelectedArtifact] = useState(null)
  const [detail, setDetail]                     = useState(null)
  const [health, setHealth]                     = useState("loading")
  const [requesterId, setRequesterId]           = useState("codebase_auditor_agent")
  const [loading, setLoading]                   = useState(false)
  const [detailLoading, setDetailLoading]       = useState(false)
  const [deleting, setDeleting]                 = useState(null)
  const [error, setError]                       = useState(null)

  // ── Health check (runs once on mount, then every 30s) ──────────────────────
  const checkHealth = useCallback(async () => {
    try {
      const res = await fetch(`${API}/health`)
      const json = await res.json()
      setHealth(json.status === "ok" ? "ok" : "db_unavailable")
    } catch {
      setHealth("db_unavailable")
    }
  }, [])

  useEffect(() => {
    checkHealth()
    const id = setInterval(checkHealth, 30_000)
    return () => clearInterval(id)
  }, [checkHealth])

  // ── Fetch artifact list ────────────────────────────────────────────────────
  const fetchArtifacts = useCallback(async () => {
    if (!requesterId.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(
        `${API}/artifacts/?requester_id=${encodeURIComponent(requesterId)}`
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      setArtifacts(json.artifacts ?? [])
    } catch (e) {
      setError(`Failed to fetch artifacts: ${e.message}`)
      setArtifacts([])
    } finally {
      setLoading(false)
    }
  }, [requesterId])

  // Fetch on mount and when requesterId changes
  useEffect(() => { fetchArtifacts() }, [fetchArtifacts])

  // ── Fetch artifact detail ──────────────────────────────────────────────────
  const handleSelect = useCallback(async (artifact) => {
    // Toggle off if same artifact clicked again
    if (selectedArtifact?.artifact_id === artifact.artifact_id) {
      setSelectedArtifact(null)
      setDetail(null)
      return
    }
    setSelectedArtifact(artifact)
    setDetail(null)
    setDetailLoading(true)
    try {
      const res = await fetch(
        `${API}/artifacts/${artifact.artifact_id}?requester_id=${encodeURIComponent(requesterId)}`
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      setDetail(json)
    } catch (e) {
      setDetail({ data: `Error fetching detail: ${e.message}` })
    } finally {
      setDetailLoading(false)
    }
  }, [selectedArtifact, requesterId])

  // ── Delete artifact ────────────────────────────────────────────────────────
  const handleDelete = useCallback(async (artifactId) => {
    if (!window.confirm(`Delete artifact ${artifactId}?`)) return
    setDeleting(artifactId)
    try {
      const res = await fetch(
        `${API}/artifacts/${artifactId}?requester_id=${encodeURIComponent(requesterId)}`,
        { method: "DELETE" }
      )
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      // Remove from local state immediately
      setArtifacts(prev => prev.filter(a => a.artifact_id !== artifactId))
      if (selectedArtifact?.artifact_id === artifactId) {
        setSelectedArtifact(null)
        setDetail(null)
      }
    } catch (e) {
      setError(`Delete failed: ${e.message}`)
    } finally {
      setDeleting(null)
    }
  }, [requesterId, selectedArtifact])

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
      <Header health={health} />

      <StatsBar artifacts={artifacts} />

      {/* Toolbar — requester ID input + refresh */}
      <div className="flex items-center gap-3 px-6 pb-3">
        <label className="text-gray-500 text-xs whitespace-nowrap">Requester ID</label>
        <input
          type="text"
          value={requesterId}
          onChange={e => setRequesterId(e.target.value)}
          onKeyDown={e => e.key === "Enter" && fetchArtifacts()}
          placeholder="e.g. codebase_auditor_agent"
          className="flex-1 max-w-xs bg-gray-900 border border-gray-700 rounded-lg px-3 py-1.5
                     text-sm text-gray-200 placeholder-gray-600 focus:outline-none
                     focus:border-indigo-500 transition-colors"
        />
        <button
          onClick={fetchArtifacts}
          disabled={loading}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white
                     text-sm px-4 py-1.5 rounded-lg transition-colors"
        >
          {loading ? "Loading…" : "Refresh"}
        </button>

        {artifacts.length > 0 && (
          <span className="text-gray-600 text-xs ml-auto">
            {artifacts.length} artifact{artifacts.length !== 1 ? "s" : ""} visible
          </span>
        )}
      </div>

      {/* Error banner */}
      {error && (
        <div className="mx-6 mb-3 px-4 py-2 bg-red-900/30 border border-red-500/30 rounded-lg text-red-300 text-sm flex justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-200">✕</button>
        </div>
      )}

      {/* Artifacts table */}
      <ArtifactTable
        artifacts={artifacts}
        selectedId={selectedArtifact?.artifact_id}
        onSelect={handleSelect}
        onDelete={handleDelete}
        deleting={deleting}
      />

      {/* Detail panel — shown below table when an artifact is selected */}
      {selectedArtifact && (
        <div className="mt-4">
          <DetailPanel
            artifact={selectedArtifact}
            detail={detail}
            loading={detailLoading}
            onClose={() => { setSelectedArtifact(null); setDetail(null) }}
          />
        </div>
      )}

      <div className="flex-1" />

      {/* Footer */}
      <footer className="px-6 py-3 border-t border-gray-800 text-center text-gray-700 text-xs">
        MCP Artifact Store · v1 · FastAPI + PostgreSQL + FastMCP
      </footer>
    </div>
  )
}

export default App
