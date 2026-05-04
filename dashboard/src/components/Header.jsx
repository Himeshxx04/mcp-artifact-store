/**
 * Header — project title + live health status dot.
 * health: 'loading' | 'ok' | 'db_unavailable'
 */

function Header({ health }) {
  const dot = {
    loading:        "bg-yellow-400 animate-pulse",
    ok:             "bg-emerald-400",
    db_unavailable: "bg-red-500",
  }[health] ?? "bg-gray-500"

  const label = {
    loading:        "Checking…",
    ok:             "All systems operational",
    db_unavailable: "DB unreachable",
  }[health] ?? "Unknown"

  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-950">
      <div className="flex items-center gap-3">
        {/* Icon */}
        <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-sm">
          A
        </div>
        <div>
          <h1 className="text-white font-semibold text-lg leading-none">
            MCP Artifact Store
          </h1>
          <p className="text-gray-500 text-xs mt-0.5">
            Multi-agent context store — v1
          </p>
        </div>
      </div>

      {/* Health indicator */}
      <div className="flex items-center gap-2 bg-gray-900 px-3 py-1.5 rounded-full border border-gray-800">
        <span className={`w-2 h-2 rounded-full ${dot}`} />
        <span className="text-gray-300 text-xs">{label}</span>
      </div>
    </header>
  )
}

export default Header
