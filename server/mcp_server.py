import os
from server.tools.artifacts import mcp

if __name__ == "__main__":
    # Local: stdio transport (default)
    # Deployed (Render): SSE transport over HTTP
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8001))

    if transport == "sse":
        mcp.run(transport="sse", host=host, port=port)
    else:
        mcp.run()  # stdio — used by LangGraph demo locally

