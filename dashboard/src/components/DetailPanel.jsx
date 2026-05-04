/**
 * DetailPanel — slide-in panel showing full artifact detail with formatted JSON.
 * Appears at the bottom of the page when an artifact row is clicked.
 */

import JsonViewer from "./JsonViewer"

function DetailPanel({ artifact, detail, loading, onClose }) {
  // Try to parse the data as JSON for pretty display; fall back to raw string
  let parsed = null
  let parseError = false
  if (detail?.data) {
    try {
      parsed = JSON.parse(detail.data)
    } catch {
      parseError = true
    }
  }

  return (
    <div className="mx-6 mb-6 rounded-xl border border-indigo-500/30 bg-gray-900 overflow-hidden">
      {/* Panel header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-gray-800 bg-gray-950">
        <div className="flex items-center gap-3">
          <span className="w-2 h-2 rounded-full bg-indigo-400" />
          <span className="font-mono text-indigo-300 text-sm">{artifact.artifact_id}</span>
          <span className="text-gray-600 text-xs">·</span>
          <span className="text-gray-400 text-xs">created by {artifact.created_by}</span>
          <span className="text-gray-600 text-xs">·</span>
          <span className="text-gray-400 text-xs">{artifact.size_bytes} bytes</span>
        </div>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-white transition-colors text-sm px-2 py-1 rounded hover:bg-gray-800"
        >
          ✕ Close
        </button>
      </div>

      {/* Context saved callout */}
      <div className="px-5 py-2 bg-indigo-950/30 border-b border-indigo-500/20 flex items-center gap-2">
        <span className="text-indigo-400 text-xs">🗜️</span>
        <span className="text-indigo-300 text-xs">
          <strong>{artifact.size_bytes} bytes</strong> stored here —
          only <strong>12 bytes</strong> (artifact_id) traveled between agents.
          Context saved: <strong>{artifact.size_bytes - 12} bytes</strong>.
        </span>
      </div>

      {/* Data viewer */}
      <div className="p-5 font-mono text-xs leading-relaxed overflow-x-auto max-h-96 overflow-y-auto">
        {loading && (
          <p className="text-gray-500 animate-pulse">Fetching artifact data…</p>
        )}
        {!loading && !detail && (
          <p className="text-gray-500">No data returned.</p>
        )}
        {!loading && detail && parseError && (
          <pre className="text-gray-300 whitespace-pre-wrap">{detail.data}</pre>
        )}
        {!loading && detail && !parseError && parsed && (
          <JsonViewer data={parsed} />
        )}
      </div>
    </div>
  )
}

export default DetailPanel
