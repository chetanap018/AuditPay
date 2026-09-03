from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

from backend.core.audit_trail import audit_trail
from backend.db.models import IdempotencyKey
from backend.db.session import SessionLocal

DEFAULT_IDEMPOTENCY_TTL = 86400


@dataclass
class IdempotencyRecord:
    key: str
    response_status: int
    response_body: dict[str, Any]
    created_at: datetime
    expires_at: datetime


class IdempotencyManager:
    def __init__(self, ttl_seconds: int = DEFAULT_IDEMPOTENCY_TTL) -> None:
        self.ttl_seconds = ttl_seconds

    def check_idempotency(self, idempotency_key: str) -> Optional[IdempotencyRecord]:
        """Check if an idempotency key was already used (DB-backed)."""
        db = SessionLocal()
        try:
            record = (
                db.query(IdempotencyKey)
                .filter(IdempotencyKey.key == idempotency_key)
                .first()
            )
            if record is None:
                return None
            # Expired keys are treated as unused
            if record.expires_at and record.expires_at < datetime.utcnow():
                return None
            response_body = json.loads(record.response) if record.response else {}
            return IdempotencyRecord(
                key=record.key,
                response_status=200,
                response_body=response_body,
                created_at=record.created_at,
                expires_at=record.expires_at or (record.created_at + timedelta(seconds=self.ttl_seconds)),
            )
        finally:
            db.close()

    def store_idempotency_response(self, idempotency_key: str, status_code: int, response_body: dict[str, Any]) -> None:
        """Persist an idempotency key with its response and record in audit trail."""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            record = IdempotencyKey(
                key=idempotency_key,
                key_id=hashlib.sha256(idempotency_key.encode()).hexdigest()[:32],
                endpoint="/api/checkout",
                response=json.dumps(response_body),
                created_at=now,
                expires_at=now + timedelta(seconds=self.ttl_seconds),
            )
            db.add(record)
            db.commit()
        finally:
            db.close()

        audit_trail.add_entry(
            event_type="idempotency_stored",
            details={
                "idempotency_key": idempotency_key,
                "status_code": status_code,
                "ttl_seconds": self.ttl_seconds,
            },
        )

    def validate_key_format(self, idempotency_key: str) -> tuple[bool, Optional[str]]:
        if not idempotency_key:
            return False, "Idempotency key is required"
        if len(idempotency_key) < 8:
            return False, "Idempotency key must be at least 8 characters"
        if len(idempotency_key) > 128:
            return False, "Idempotency key must not exceed 128 characters"
        if not all(c.isalnum() or c in "-_" for c in idempotency_key):
            return False, "Idempotency key contains invalid characters"
        return True, None

    def generate_key(self, data: dict[str, Any]) -> str:
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def cleanup_expired(self) -> int:
        now = datetime.utcnow()
        db = SessionLocal()
        try:
            result = db.query(IdempotencyKey).filter(IdempotencyKey.expires_at < now).delete()
            db.commit()
            return result
        finally:
            db.close()


idempotency_manager = IdempotencyManager()
