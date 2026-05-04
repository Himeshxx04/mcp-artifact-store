/**
 * StatsBar — four stat cards including the hero "context saved" metric.
 *
 * Context saved calculation:
 *   Each artifact travels through agent graphs as just its artifact_id
 *   (e.g. "art_8eb369b0" = 12 bytes). Without the store the full payload
 *   would travel. So context saved per artifact = size_bytes - 12.
 */

const ARTIFACT_ID_BYTES = 12 // "art_xxxxxxxx"

function fmt(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

function StatCard({ icon, label, value, sub, accent }) {
  return (
    <div className={`flex-1 bg-gray-900 border rounded-xl px-5 py-4 ${accent ? "border-indigo-500/40" : "border-gray-800"}`}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{icon}</span>
        <span className="text-gray-400 text-xs uppercase tracking-wider">{label}</span>
      </div>
      <p className={`text-2xl font-semibold ${accent ? "text-indigo-300" : "text-white"}`}>
        {value}
      </p>
      {sub && <p className="text-gray-500 text-xs mt-1">{sub}</p>}
    </div>
  )
}

function StatsBar({ artifacts }) {
  const count = artifacts.length
  const totalBytes = artifacts.reduce((s, a) => s + (a.size_bytes ?? 0), 0)
  const contextSaved = Math.max(0, totalBytes - count * ARTIFACT_ID_BYTES)

  const now = Date.now()
  const expiringSoon = artifacts.filter(a => {
    // Append Z so the browser treats the naive UTC string as UTC
    const raw = a.expires_at.endsWith("Z") ? a.expires_at : a.expires_at + "Z"
    const exp = new Date(raw).getTime()
    return exp > now && exp - now < 60 * 60 * 1000 // within 1 hour
  }).length

  return (
    <div className="flex gap-4 px-6 py-4">
      <StatCard
        icon="📦"
        label="Artifacts stored"
        value={count}
        sub="non-expired, visible to you"
      />
      <StatCard
        icon="💾"
        label="Total stored"
        value={fmt(totalBytes)}
        sub="across all artifacts"
      />
      <StatCard
        icon="🗜️"
        label="Context saved"
        value={fmt(contextSaved)}
        sub={`vs ${count * ARTIFACT_ID_BYTES} bytes in graph state`}
        accent
      />
      <StatCard
        icon="⏳"
        label="Expiring soon"
        value={expiringSoon}
        sub="within the next hour"
      />
    </div>
  )
}

export default StatsBar
