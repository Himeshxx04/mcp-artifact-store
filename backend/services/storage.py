from fastapi import HTTPException
from datetime import datetime, timedelta
from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session
from backend.models.artifact import Artifact
from backend.models.audit_log import AuditLog
import uuid


def write_artifact(
    data: str,
    created_by: str,
    ttl_seconds: int,
    allowed_readers: list[str],
    db: Session
) -> dict:
    # Step 1 — generate artifact_id
    artifact_id = f"art_{uuid.uuid4().hex[:8]}"

    # Step 2 — calculate expires_at
    expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

    # Step 3 — calculate size
    size_bytes = len(data.encode("utf-8"))

    # Step 4 — create artifact object
    artifact = Artifact(
        artifact_id=artifact_id,
        data=data,
        created_by=created_by,
        allowed_readers=allowed_readers,
        expires_at=expires_at,
        size_bytes=size_bytes
    )

    # Step 5 — save artifact + audit log in one atomic transaction
    log = AuditLog(
        artifact_id=artifact_id,
        action="WRITE",
        requester_id=created_by,
        success=True
    )
    try:
        db.add(artifact)
        db.add(log)
        db.commit()
        db.refresh(artifact)
    except Exception as e:
        db.rollback()
        raise e

    return {
        "artifact_id": artifact_id,
        "created_by": created_by,
        "expires_at": expires_at.isoformat(),
        "size_bytes": size_bytes
    }


def read_artifact(
    artifact_id: str,
    requester_id: str,
    db: Session
) -> dict:
    artifact = db.query(Artifact).filter(Artifact.artifact_id == artifact_id).first()

    if artifact is None:
        log = AuditLog(
            artifact_id=artifact_id,
            action="READ",
            requester_id=requester_id,
            success=False,
            reason="Not Found"
        )
        db.add(log)
        db.commit()
        raise HTTPException(status_code=404, detail="Artifact not found")

    if datetime.utcnow() > artifact.expires_at:
        log = AuditLog(
            artifact_id=artifact_id,
            action="READ",
            requester_id=requester_id,
            success=False,
            reason="Expired"
        )
        db.add(log)
        db.commit()
        raise HTTPException(status_code=410, detail="Artifact has expired")

    if requester_id not in (artifact.allowed_readers or []):
        log = AuditLog(
            artifact_id=artifact_id,
            action="READ",
            requester_id=requester_id,
            success=False,
            reason="Not authorized"
        )
        db.add(log)
        db.commit()
        raise HTTPException(status_code=403, detail="Not allowed to read")

    log = AuditLog(
        artifact_id=artifact_id,
        action="READ",
        requester_id=requester_id,
        success=True
    )
    db.add(log)
    db.commit()

    return {"data": artifact.data}


def list_artifacts(
    requester_id: str,
    db: Session
) -> dict:
    visible = db.query(Artifact).filter(
        Artifact.expires_at > datetime.utcnow(),
        cast(Artifact.allowed_readers, JSONB).contains([requester_id])
    ).all()

    log = AuditLog(
        artifact_id=None,       # No single artifact for LIST action
        action="LIST",
        requester_id=requester_id,
        success=True
    )
    db.add(log)
    db.commit()

    return {
        "artifacts": [
            {
                "artifact_id": a.artifact_id,
                "created_by": a.created_by,
                "expires_at": a.expires_at.isoformat(),
                "size_bytes": a.size_bytes
            }
            for a in visible
        ],
        "count": len(visible)
    }


def delete_artifact(
    artifact_id: str,
    requester_id: str,
    db: Session
) -> dict:
    artifact = db.query(Artifact).filter(Artifact.artifact_id == artifact_id).first()

    if artifact is None:
        log = AuditLog(
            artifact_id=artifact_id,
            action="DELETE",
            requester_id=requester_id,
            success=False,
            reason="Not Found"
        )
        db.add(log)
        db.commit()
        raise HTTPException(status_code=404, detail="Artifact not found")

    if requester_id != artifact.created_by:
        log = AuditLog(
            artifact_id=artifact_id,
            action="DELETE",
            requester_id=requester_id,
            success=False,
            reason="Not authorized"
        )
        db.add(log)
        db.commit()
        raise HTTPException(status_code=403, detail="Unauthorized action")

    log = AuditLog(
        artifact_id=artifact_id,
        action="DELETE",
        requester_id=requester_id,
        success=True
    )
    db.add(log)
    db.delete(artifact)
    db.commit()

    return {"message": "Artifact deleted successfully"}