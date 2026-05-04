import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from backend.models.base import Base



class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id = Column(String, nullable=False, unique=True)
    data = Column(String, nullable=False)
    created_by = Column(String, nullable=False)
    allowed_readers = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    size_bytes = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Artifact {self.artifact_id} created_by={self.created_by}>"