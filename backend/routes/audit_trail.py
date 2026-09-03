from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.audit_trail import audit_trail
from backend.db.session import get_db

router = APIRouter(prefix="/audit-trail", tags=["audit-trail"])


@router.get("/events")
def get_audit_events(
    limit: int = 100,
    offset: int = 0,
    event_type: Optional[str] = None,
) -> dict:
    """Get immutable audit trail events."""
    events = audit_trail.get_trail(event_type=event_type, limit=limit)
    return {"events": events, "count": len(events)}


@router.get("/verify")
def verify_audit_integrity() -> dict:
    """Verify the integrity of the audit trail."""
    return audit_trail.verify_integrity()


@router.get("/stats")
def get_audit_stats() -> dict:
    """Get audit trail statistics."""
    integrity = audit_trail.verify_integrity()
    return {
        "total_entries": integrity["total_entries"],
        "is_valid": integrity["is_valid"],
        "verified_at": integrity["verified_at"],
    }
