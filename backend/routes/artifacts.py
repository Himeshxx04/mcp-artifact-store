from sqlalchemy.orm import Session
from fastapi import Depends, APIRouter
from backend.db.session import get_db
from backend.schemas import artifacts as artifact_schemas
from backend.services.storage import (
    write_artifact,
    read_artifact,
    list_artifacts,
    delete_artifact
)

router = APIRouter(
    prefix="/artifacts",
    tags=["Artifacts"]
)


@router.post("/", response_model=artifact_schemas.WriteArtifactResponse)
def write_artifact_endpoint(
    payload: artifact_schemas.WriteArtifactRequest,
    db: Session = Depends(get_db)
):
    return write_artifact(
        data=payload.data,
        created_by=payload.created_by,
        ttl_seconds=payload.ttl_seconds,
        allowed_readers=payload.allowed_readers,
        db=db
    )


@router.get("/", response_model=artifact_schemas.ListArtifactsResponse)
def list_artifacts_endpoint(
    requester_id: str,
    db: Session = Depends(get_db)
):
    return list_artifacts(requester_id=requester_id, db=db)


@router.get("/{artifact_id}", response_model=artifact_schemas.ReadArtifactResponse)
def read_artifact_endpoint(
    artifact_id: str,
    requester_id: str,
    db: Session = Depends(get_db)
):
    return read_artifact(artifact_id=artifact_id, requester_id=requester_id, db=db)


@router.delete("/{artifact_id}")
def delete_artifact_endpoint(
    artifact_id: str,
    requester_id: str,
    db: Session = Depends(get_db)
):
    return delete_artifact(artifact_id=artifact_id, requester_id=requester_id, db=db)