from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Optional

from backend.db.models import AuditLog
from backend.db.session import SessionLocal


class ImmutableAuditTrail:
    """Provides tamper-evident audit trail with hash chaining."""

    def __init__(self) -> None:
        self._last_hash: str = ""

    def _compute_hash(self, data: dict[str, Any], previous_hash: str) -> str:
        """Compute SHA-256 hash of audit entry including previous hash for chaining."""
        content = json.dumps(data, sort_keys=True) + previous_hash
        return hashlib.sha256(content.encode()).hexdigest()

    def _get_last_hash(self) -> str:
        """Get the hash of the most recent audit entry."""
        db = SessionLocal()
        try:
            last_entry = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
            if last_entry and last_entry.details:
                details = json.loads(last_entry.details)
                return details.get("entry_hash", "")
            return ""
        finally:
            db.close()

    def add_entry(
        self,
        event_type: str,
        details: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Add an immutable entry to the audit trail.
        
        Args:
            event_type: Type of event being recorded
            details: Event details dictionary
            
        Returns:
            The complete audit entry with hash information
        """
        previous_hash = self._get_last_hash()

        entry = {
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
            "previous_hash": previous_hash,
        }

        entry_hash = self._compute_hash(entry, previous_hash)
        entry["entry_hash"] = entry_hash

        # Store in database
        db = SessionLocal()
        try:
            audit = AuditLog(
                event_type=event_type,
                details=json.dumps(entry),
            )
            db.add(audit)
            db.commit()
        finally:
            db.close()

        return entry

    def verify_integrity(self) -> dict[str, Any]:
        """
        Verify the integrity of the entire audit trail.
        
        Returns:
            Verification result with status and any issues found
        """
        db = SessionLocal()
        try:
            entries = db.query(AuditLog).order_by(AuditLog.id.asc()).all()

            issues: list[str] = []
            previous_hash = ""

            for i, entry in enumerate(entries):
                if not entry.details:
                    issues.append(f"Entry {i+1}: Missing details")
                    continue

                stored_data = json.loads(entry.details)
                stored_hash = stored_data.get("entry_hash", "")
                stored_previous_hash = stored_data.get("previous_hash", "")

                if stored_previous_hash != previous_hash:
                    issues.append(
                        f"Entry {i+1} ({entry.event_type}): Hash chain broken. "
                        f"Expected previous_hash={previous_hash}, got {stored_previous_hash}"
                    )

                # Recompute hash to verify
                entry_copy = {k: v for k, v in stored_data.items() if k != "entry_hash"}
                computed_hash = self._compute_hash(entry_copy, stored_previous_hash)

                if computed_hash != stored_hash:
                    issues.append(
                        f"Entry {i+1} ({entry.event_type}): Hash mismatch. "
                        f"Entry may have been tampered with."
                    )

                previous_hash = stored_hash

            return {
                "is_valid": len(issues) == 0,
                "total_entries": len(entries),
                "issues": issues,
                "verified_at": datetime.utcnow().isoformat(),
            }
        finally:
            db.close()

    def get_trail(
        self,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get audit trail entries with optional filtering."""
        db = SessionLocal()
        try:
            query = db.query(AuditLog).order_by(AuditLog.id.desc())

            if event_type:
                query = query.filter(AuditLog.event_type == event_type)

            entries = query.limit(limit).all()

            result = []
            for entry in entries:
                if entry.details:
                    data = json.loads(entry.details)
                    result.append({
                        "id": entry.id,
                        "event_type": entry.event_type,
                        "timestamp": entry.created_at.isoformat(),
                        "details": data.get("details", {}),
                        "entry_hash": data.get("entry_hash", ""),
                    })
            return result
        finally:
            db.close()


# Singleton instance
audit_trail = ImmutableAuditTrail()
