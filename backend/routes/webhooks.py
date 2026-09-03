from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from backend.core.webhook_security import webhook_security

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/razorpay")
async def razorpay_webhook(request: Request) -> dict:
    """
    Handle Razorpay webhook events.

    This endpoint:
    1. Verifies webhook signature (prevents spoofing)
    2. Validates timestamp (prevents replay attacks)
    3. Checks for duplicate events (idempotency)
    4. Processes valid events
    """
    # Get signature from header
    signature = request.headers.get("x-razorpay-signature", "")
    timestamp = request.headers.get("x-razorpay-request-timestamp", None)

    # Read raw body
    body = await request.body()

    # Verify webhook
    result = webhook_security.verify_webhook(
        payload=body,
        signature=signature,
        timestamp=timestamp,
    )

    if not result.is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Webhook verification failed",
                "reason": result.error,
                "is_duplicate": result.is_duplicate,
            },
        )

    # Process the event based on type
    event_type = result.event_type
    if event_type == "payment.captured":
        await _handle_payment_captured(result.payload)
    elif event_type == "payment.failed":
        await _handle_payment_failed(result.payload)
    elif event_type == "order.paid":
        await _handle_order_paid(result.payload)
    elif event_type == "refund.created":
        await _handle_refund_created(result.payload)

    return {
        "status": "processed",
        "event_id": result.event_id,
        "event_type": event_type,
    }


async def _handle_payment_captured(payload: dict) -> None:
    """Handle successful payment capture."""
    from backend.core.audit_trail import audit_trail

    payment = payload.get("payload", {}).get("payment", {}).get("entity", {})
    audit_trail.add_entry(
        event_type="payment_captured",
        details={
            "payment_id": payment.get("id"),
            "amount": payment.get("amount"),
            "currency": payment.get("currency"),
            "method": payment.get("method"),
        },
    )


async def _handle_payment_failed(payload: dict) -> None:
    """Handle failed payment."""
    from backend.core.audit_trail import audit_trail

    payment = payload.get("payload", {}).get("payment", {}).get("entity", {})
    audit_trail.add_entry(
        event_type="payment_failed",
        details={
            "payment_id": payment.get("id"),
            "error_code": payment.get("error_code"),
            "error_description": payment.get("error_description"),
        },
    )


async def _handle_order_paid(payload: dict) -> None:
    """Handle order fully paid."""
    from backend.core.audit_trail import audit_trail

    order = payload.get("payload", {}).get("order", {}).get("entity", {})
    audit_trail.add_entry(
        event_type="order_paid",
        details={
            "order_id": order.get("id"),
            "amount_paid": order.get("amount_paid"),
        },
    )


async def _handle_refund_created(payload: dict) -> None:
    """Handle refund creation."""
    from backend.core.audit_trail import audit_trail

    refund = payload.get("payload", {}).get("refund", {}).get("entity", {})
    audit_trail.add_entry(
        event_type="refund_created",
        details={
            "refund_id": refund.get("id"),
            "payment_id": refund.get("payment_id"),
            "amount": refund.get("amount"),
        },
    )
