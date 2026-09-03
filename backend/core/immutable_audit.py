from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from backend.db.models import AuditLog
from backend.db.session import SessionLocal


@dataclass
class AuditEntry:
    """Immutable audit entry with hash chain verification."""
    id: int
    event_type: str
    details: str
    created_at: datetime
    entry_hash: str
    previous_hash: Optional[str]


class ImmutableAuditTrail:
    """
    Implements an append-only audit trail using hash chaining.
    
    Each audit entry contains a hash of its content plus the hash of the
    previous entry, creating a tamper-evident chain similar to blockchain.
    This ensures that any modification to historical records is detectable.
    """

    def __init__(self) -> None:
        self._last_hash: Optional[str] = None
        self._initialize_chain()

    def _initialize_chain(self) -> None:
        """Initialize the hash chain from existing records."""
        db = SessionLocal()
        try:
            last_entry = (
                db.query(AuditLog)
                .order_by(AuditLog.id.desc())
                .first()
            )
            if last_entry:
                self._last_hash = self._calculate_hash(last_entry)
        finally:
            db.close()

    def _calculate_hash(self, entry: AuditLog) -> str:
        """Calculate SHA-256 hash of an audit entry."""
        hash_data = {
            "id": entry.id,
            "event_type": entry.event_type,
            "details": entry.details,
            "created_at": entry.created_at.isoformat(),
            "previous_hash": self._last_hash,
        }
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def _calculate_entry_hash(
        self,
        event_type: str,
        details: str,
        timestamp: datetime,
        previous_hash: Optional[str],
    ) -> str:
        """Calculate hash for a new entry before it's stored."""
        hash_data = {
            "event_type": event_type,
            "details": details,
            "created_at": timestamp.isoformat(),
            "previous_hash": previous_hash,
        }
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()
