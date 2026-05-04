from datetime import datetime
from typing import List
from pydantic import Field, BaseModel


# ─── Request Schemas ───────────────────────────────────────────────

class WriteArtifactRequest(BaseModel):
    data: str
    created_by: str
    ttl_seconds: int = Field(gt=0)
    allowed_readers: list[str]


# ─── Response Schemas ──────────────────────────────────────────────

class ArtifactSummary(BaseModel):
    artifact_id: str
    created_by: str
    expires_at: datetime
    size_bytes: int


class WriteArtifactResponse(BaseModel):
    artifact_id: str
    created_by: str
    expires_at: datetime
    size_bytes: int


class ReadArtifactResponse(BaseModel):
    data: str


class ListArtifactsResponse(BaseModel):
    artifacts: List[ArtifactSummary]
    count: int