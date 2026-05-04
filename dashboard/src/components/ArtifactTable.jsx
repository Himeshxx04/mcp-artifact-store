/**
 * ArtifactTable — lists all visible artifacts with click-to-inspect and delete.
 */

function parseUTC(isoString) {
  // Backend returns naive UTC datetimes without a timezone suffix.
  // Appending "Z" tells the browser to treat it as UTC instead of local time.
  if (!isoString.endsWith("Z") && !isoString.includes("+")) {
    return new Date(isoString + "Z")
  }
  return new Date(isoString)
}

function timeLabel(isoString) {
  const diff = parseUTC(isoString).getTime() - Date.now()
  const abs = Math.abs(diff)
  const mins = Math.floor(abs / 60000)
  const hrs = Math.floor(abs / 3600000)
  const days = Math.floor(abs / 86400000)

  const label =
    abs < 60000   ? "< 1m"       :
    abs < 3600000 ? `${mins}m`   :
    abs < 86400000 ? `${hrs}h`   :
    `${days}d`

  return diff > 0
    ? { text: `in ${label}`, expired: false }
    : { text: `${label} ago`, expired: true }
}

function fmt(bytes) {
  if (bytes < 1024) return `${bytes} B`
  return `${(bytes / 1024).toFixed(1)} KB`
}

function ArtifactTable({ artifacts, selectedId, onSelect, onDelete, deleting }) {
  if (artifacts.length === 0) {
    return (
      <div className="mx-6 rounded-xl border border-gray-800 bg-gray-900 p-12 text-center">
        <p className="text-gray-500 text-sm">No artifacts found for this requester ID.</p>
        <p className="text-gray-600 text-xs mt-1">
          Run the codebase auditor demo, then refresh.
        </p>
      </div>
    )
  }

  return (
    <div className="mx-6 rounded-xl border border-gray-800 overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-900 border-b border-gray-800">
            <th className="text-left px-4 py-3 text-gray-400 font-medium">Artifact ID</th>
            <th className="text-left px-4 py-3 text-gray-400 font-medium">Created by</th>
            <th className="text-right px-4 py-3 text-gray-400 font-medium">Size</th>
            <th className="text-right px-4 py-3 text-gray-400 font-medium">Expires</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody>
          {artifacts.map((a, i) => {
            const { text, expired } = timeLabel(a.expires_at)
            const isSelected = a.artifact_id === selectedId
            return (
              <tr
                key={a.artifact_id}
                onClick={() => onSelect(a)}
                className={`border-b border-gray-800 cursor-pointer transition-colors
                  ${i % 2 === 0 ? "bg-gray-950" : "bg-gray-900/50"}
                  ${isSelected ? "bg-indigo-950/40 border-l-2 border-l-indigo-500" : "hover:bg-gray-800/50"}`}
              >
                <td className="px-4 py-3 font-mono text-indigo-300">
                  {a.artifact_id}
                </td>
                <td className="px-4 py-3 text-gray-300">
                  {a.created_by}
                </td>
                <td className="px-4 py-3 text-right text-gray-300">
                  {fmt(a.size_bytes)}
                </td>
                <td className={`px-4 py-3 text-right text-xs ${expired ? "text-red-400" : "text-emerald-400"}`}>
                  {text}
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={e => { e.stopPropagation(); onDelete(a.artifact_id) }}
                    disabled={deleting === a.artifact_id}
                    className="text-gray-600 hover:text-red-400 transition-colors text-xs px-2 py-1 rounded hover:bg-red-400/10 disabled:opacity-40"
                  >
                    {deleting === a.artifact_id ? "…" : "Delete"}
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default ArtifactTable
