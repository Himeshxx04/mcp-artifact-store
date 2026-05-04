from backend.db.session import SessionLocal
from backend.services.storage import (
    write_artifact,
    read_artifact,
    list_artifacts,
    delete_artifact
)
from fastmcp import FastMCP

mcp = FastMCP("mcp-artifact-store")


def get_session():
    return SessionLocal()


@mcp.tool()
def write_artifact_tool(
    data: str,
    created_by: str,
    ttl_seconds: int,
    allowed_readers: list[str]
) -> dict:
    """Write a large artifact into the store. Returns artifact_id to pass between agents instead of raw data."""
    db = get_session()
    try:
        return write_artifact(
            data=data,
            created_by=created_by,
            ttl_seconds=ttl_seconds,
            allowed_readers=allowed_readers,
            db=db
        )
    finally:
        db.close()


@mcp.tool()
def read_artifact_tool(
    artifact_id: str,
    requester_id: str
) -> dict:
    """Read an artifact from the store using its artifact_id. Only works if requester_id is in allowed_readers."""
    db = get_session()
    try:
        return read_artifact(
            artifact_id=artifact_id,
            requester_id=requester_id,
            db=db
        )
    finally:
        db.close()


@mcp.tool()
def list_artifacts_tool(
    requester_id: str
) -> dict:
    """List all non-expired artifacts this requester is allowed to read."""
    db = get_session()
    try:
        return list_artifacts(
            requester_id=requester_id,
            db=db
        )
    finally:
        db.close()


@mcp.tool()
def delete_artifact_tool(
    artifact_id: str,
    requester_id: str
) -> dict:
    """Delete an artifact. Only the original creator can delete it."""
    db = get_session()
    try:
        return delete_artifact(
            artifact_id=artifact_id,
            requester_id=requester_id,
            db=db
        )
    finally:
        db.close()