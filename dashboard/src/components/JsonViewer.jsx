/**
 * JsonViewer — recursive syntax-highlighted JSON renderer.
 * No external library. Colors match a dark terminal aesthetic.
 */

function JsonViewer({ data, depth = 0 }) {
  const indent = "  ".repeat(depth)
  const childIndent = "  ".repeat(depth + 1)

  if (data === null)
    return <span className="text-gray-500">null</span>

  if (typeof data === "boolean")
    return <span className="text-yellow-400">{String(data)}</span>

  if (typeof data === "number")
    return <span className="text-blue-400">{data}</span>

  if (typeof data === "string")
    return <span className="text-emerald-400">"{data}"</span>

  if (Array.isArray(data)) {
    if (data.length === 0)
      return <span className="text-gray-400">[]</span>
    return (
      <span>
        <span className="text-gray-400">[</span>
        {data.map((item, i) => (
          <div key={i} className="ml-4">
            <JsonViewer data={item} depth={depth + 1} />
            {i < data.length - 1 && <span className="text-gray-500">,</span>}
          </div>
        ))}
        <span className="text-gray-400">{indent}]</span>
      </span>
    )
  }

  if (typeof data === "object") {
    const entries = Object.entries(data)
    if (entries.length === 0)
      return <span className="text-gray-400">{"{}"}</span>
    return (
      <span>
        <span className="text-gray-400">{"{"}</span>
        {entries.map(([key, value], i) => (
          <div key={key} className="ml-4">
            <span className="text-violet-400">"{key}"</span>
            <span className="text-gray-400">: </span>
            <JsonViewer data={value} depth={depth + 1} />
            {i < entries.length - 1 && <span className="text-gray-500">,</span>}
          </div>
        ))}
        <span className="text-gray-400">{indent}{"}"}</span>
      </span>
    )
  }

  return <span className="text-gray-300">{String(data)}</span>
}

export default JsonViewer
