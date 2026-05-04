from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.routes.artifacts import router
from backend.db.session import get_db
import os
import uvicorn

app = FastAPI(
    title="MCP Artifact Store",
    description="Shared artifact store for multi-agent systems. Reduces context window bloat by passing artifact IDs instead of raw data between agents.",
    version="0.1.0"
)
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "version": "0.1.0"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "db_unavailable", "version": "0.1.0"})


if __name__ == "__main__":
    # Render injects PORT; locally defaults to 8000
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)