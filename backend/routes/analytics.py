from __future__ import annotations

from fastapi import APIRouter

from backend.core.audit_trail import audit_trail
from backend.core.payment_analytics import payment_analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def get_analytics_summary() -> dict:
    """Get payment analytics summary."""
    metrics = payment_analytics.get_metrics(hours=24)
    return {
        "total_transactions": metrics.total_transactions,
        "successful_transactions": metrics.successful_transactions,
        "failed_transactions": metrics.failed_transactions,
        "blocked_transactions": metrics.blocked_transactions,
        "total_revenue": metrics.total_revenue,
        "average_order_value": metrics.average_order_value,
    }


@router.get("/hourly")
def get_hourly_trends(hours: int = 24) -> dict:
    """Get hourly transaction trends."""
    metrics = payment_analytics.get_metrics(hours=hours)
    return {
        "hourly_distribution": metrics.hourly_distribution,
        "period_hours": hours,
    }


@router.get("/failures")
def get_failure_analysis(hours: int = 24) -> dict:
    """Get failure analysis for the specified period."""
    return payment_analytics.get_failure_analysis()


@router.get("/risk-distribution")
def get_risk_distribution() -> dict:
    """Get distribution of risk scores across transactions."""
    metrics = payment_analytics.get_metrics(hours=24)
    return {
        "risk_distribution": metrics.risk_distribution,
    }


@router.get("/revenue")
def get_revenue_summary() -> dict:
    """Get revenue summary for different time periods."""
    return payment_analytics.get_revenue_summary()


@router.get("/verify-audit")
def verify_audit_trail() -> dict:
    """Verify the integrity of the immutable audit trail."""
    return audit_trail.verify_integrity()


@router.get("/trail")
def get_audit_trail(event_type: str = None, limit: int = 100) -> list[dict]:
    """Get audit trail entries with optional filtering."""
    return audit_trail.get_trail(event_type=event_type, limit=limit)
