from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from backend.core.audit_trail import audit_trail
from backend.db.models import AuditLog
from backend.db.session import SessionLocal

# Maximum age of a webhook event in seconds (5 minutes)
MAX_WEBHOOK_AGE_SECONDS = 300


@dataclass
class WebhookVerificationResult:
    """Result of webhook signature verification."""
    is_valid: bool
    event_id: Optional[str] = None
    event_type: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    is_duplicate: bool = False


class WebhookSecurity:
    """Handles webhook verification and replay attack prevention."""

    def __init__(self, webhook_secret: str = "") -> None:
        self.webhook_secret = webhook_secret
        self._processed_events: set[str] = set()

    def set_secret(self, secret: str) -> None:
        """Set the webhook secret for signature verification."""
        self.webhook_secret = secret

    def verify_webhook(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None,
    ) -> WebhookVerificationResult:
        """
        Verify Razorpay webhook signature and prevent replay attacks.
        
        Args:
            payload: Raw request body bytes
            signature: X-Razorpay-Signature header value
            timestamp: Optional timestamp for age validation
            
        Returns:
            WebhookVerificationResult with validation status
        """
        secret = self._get_secret()

        # Step 1: Validate timestamp (prevent replay attacks with old events)
        if timestamp:
            try:
                event_time = datetime.fromtimestamp(int(timestamp))
                age = (datetime.utcnow() - event_time).total_seconds()
                if age > MAX_WEBHOOK_AGE_SECONDS:
                    return WebhookVerificationResult(
                        is_valid=False,
                        error=f"Webhook event too old: {age:.0f}s (max {MAX_WEBHOOK_AGE_SECONDS}s)",
                    )
            except (ValueError, TypeError):
                return WebhookVerificationResult(
                    is_valid=False,
                    error="Invalid timestamp format",
                )

        # Step 2: Verify signature
        if not secret:
            return WebhookVerificationResult(
                is_valid=False,
                error="Webhook secret not configured (set RAZORPAY_WEBHOOK_SECRET)",
            )

        expected_signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_signature, signature):
            return WebhookVerificationResult(
                is_valid=False,
                error="Invalid webhook signature",
            )

        # Step 3: Parse payload and check for duplicate events
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return WebhookVerificationResult(
                is_valid=False,
                error="Invalid JSON payload",
            )

        event_id = self._extract_event_id(data)
        if not event_id:
            return WebhookVerificationResult(
                is_valid=False,
                error="Missing event ID in payload",
            )

        # Check for duplicate (replay attack prevention)
        if self._is_duplicate_event(event_id):
            return WebhookVerificationResult(
                is_valid=False,
                event_id=event_id,
                is_duplicate=True,
                error="Duplicate webhook event detected (replay attack prevention)",
            )

        # Mark event as processed
        self._mark_event_processed(event_id)

        # Persist to database for audit
        self._record_webhook_event(event_id, data)

        return WebhookVerificationResult(
            is_valid=True,
            event_id=event_id,
            event_type=data.get("event"),
            payload=data,
        )

    def _get_secret(self) -> str:
        """Resolve the webhook secret at call time (env may load after import)."""
        if self.webhook_secret:
            return self.webhook_secret
        return os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

    def _generate_signature(self, payload: bytes) -> str:
        """Compute the expected Razorpay signature for a payload."""
        return hmac.new(
            self._get_secret().encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()
        """Generate HMAC-SHA256 signature for webhook payload."""
        return hmac.new(
            self.webhook_secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()

    def _extract_event_id(self, data: dict[str, Any]) -> Optional[str]:
        """Extract event ID from Razorpay webhook payload."""
        # Razorpay webhook format: payload contains event and contains payment/entity info
        event = data.get("event", "")
        payload = data.get("payload", {})
        payment = payload.get("payment", {})
        entity = payment.get("entity", {})
        return entity.get("id") or data.get("id") or event

    def _is_duplicate_event(self, event_id: str) -> bool:
        """Check if event was already processed (in-memory + database)."""
        if event_id in self._processed_events:
            return True
        # Also check database for persistence across restarts
        db = SessionLocal()
        try:
            existing = db.query(AuditLog).filter(
                AuditLog.event_type == "webhook_received",
                AuditLog.details.contains(event_id)
            ).first()
            return existing is not None
        finally:
            db.close()

    def _mark_event_processed(self, event_id: str) -> None:
        """Mark event as processed in memory."""
        self._processed_events.add(event_id)
        # Limit memory usage
        if len(self._processed_events) > 10000:
            # Remove oldest events (keep most recent 5000)
            events_list = list(self._processed_events)
            self._processed_events = set(events_list[-5000:])

    def _record_webhook_event(self, event_id: str, data: dict[str, Any]) -> None:
        """Record webhook event in the immutable hash-chained audit trail."""
        audit_trail.add_entry(
            event_type="webhook_received",
            details={
                "event_id": event_id,
                "razorpay_event": data.get("event"),
                "received_at": datetime.utcnow().isoformat(),
                "payload_hash": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16],
            },
        )


# Singleton instance - load webhook secret from environment
_webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
webhook_security = WebhookSecurity(webhook_secret=_webhook_secret)
