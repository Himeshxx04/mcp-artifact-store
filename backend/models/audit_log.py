import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from backend.models.base import Base

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    requester_id = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    success = Column(Boolean, nullable=False, default=True)
    reason = Column(String, nullable=True)

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.artifact_id} by {self.requester_id}>"