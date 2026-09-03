from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

from backend.db.models import AuditLog
from backend.db.session import SessionLocal


@dataclass
class PaymentMetrics:
    total_transactions: int = 0
    successful_transactions: int = 0
    failed_transactions: int = 0
    blocked_transactions: int = 0
    total_revenue: float = 0.0
    average_order_value: float = 0.0
    risk_distribution: dict[str, int] = field(default_factory=dict)
    hourly_distribution: dict[int, int] = field(default_factory=dict)


class PaymentAnalytics:
    def __init__(self, db: Any = None) -> None:
        self._db = db

    def _get_db(self) -> SessionLocal:
        if self._db:
            return self._db
        return SessionLocal()

    def get_metrics(self, hours: int = 24) -> PaymentMetrics:
        db = self._get_db()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            logs = db.query(AuditLog).filter(AuditLog.created_at >= cutoff).all()

            metrics = PaymentMetrics()
            risk_counts: dict[str, int] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
            hourly_counts: dict[int, int] = {}

            for log in logs:
                data = json.loads(log.details) if log.details else {}
                # Support both chained entries ({"details": {...}}) and legacy flat entries
                details = data.get("details", data) if isinstance(data, dict) else {}

                if log.event_type == "checkout_approved":
                    metrics.successful_transactions += 1
                    amount = details.get("amount", 0)
                    metrics.total_revenue += amount
                    hour = log.created_at.hour
                    hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
                elif log.event_type == "payment_captured":
                    # Confirmed payment from Razorpay webhook (amount is in paise)
                    metrics.successful_transactions += 1
                    amount = float(details.get("amount", 0))
                    metrics.total_revenue += amount / 100.0
                    hour = log.created_at.hour
                    hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
                elif log.event_type == "payment_declined":
                    metrics.failed_transactions += 1
                elif log.event_type == "payment_failed":
                    metrics.failed_transactions += 1
                elif log.event_type == "checkout_blocked":
                    metrics.blocked_transactions += 1
                elif log.event_type == "risk_blocked":
                    metrics.blocked_transactions += 1
                    level = str(details.get("risk_level", "high"))
                    risk_counts[level] = risk_counts.get(level, 0) + 1
                elif log.event_type == "risk_assessment":
                    level = details.get("risk_level", "minimal")
                    risk_counts[level] = risk_counts.get(level, 0) + 1

            metrics.total_transactions = (
                metrics.successful_transactions + metrics.failed_transactions + metrics.blocked_transactions
            )

            if metrics.successful_transactions > 0:
                metrics.average_order_value = round(
                    metrics.total_revenue / metrics.successful_transactions, 2
                )

            metrics.risk_distribution = risk_counts
            metrics.hourly_distribution = hourly_counts

            return metrics
        finally:
            db.close()

    def get_dashboard_metrics(self) -> dict[str, Any]:
        """Get comprehensive dashboard metrics."""
        metrics = self.get_metrics(hours=24)
        revenue = self.get_revenue_summary()
        failures = self.get_failure_analysis()

        return {
            "transactions": {
                "total": metrics.total_transactions,
                "successful": metrics.successful_transactions,
                "failed": metrics.failed_transactions,
                "blocked": metrics.blocked_transactions,
                "success_rate": round(metrics.successful_transactions / max(metrics.total_transactions, 1) * 100, 1),
            },
            "revenue": revenue,
            "average_order_value": metrics.average_order_value,
            "risk_distribution": metrics.risk_distribution,
            "failures": failures,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def get_transaction_history(self, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        """Get detailed transaction history."""
        db = self._get_db()
        try:
            entries = (
                db.query(AuditLog)
                .filter(AuditLog.event_type.in_(["checkout_approved", "payment_declined", "checkout_blocked"]))
                .order_by(AuditLog.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            transactions = []
            for entry in entries:
                data = json.loads(entry.details) if entry.details else {}
                details = data.get("details", data) if isinstance(data, dict) else {}
                transactions.append({
                    "id": entry.id,
                    "timestamp": entry.created_at.isoformat(),
                    "event_type": entry.event_type,
                    "amount": details.get("amount"),
                    "product_id": details.get("product_id"),
                    "reason": details.get("reason"),
                    "razorpay_order_id": details.get("razorpay_order_id"),
                    "risk_score": details.get("risk_score"),
                    "risk_level": details.get("risk_level"),
                })

            return {
                "transactions": transactions,
                "limit": limit,
                "offset": offset,
                "total": len(transactions),
            }
        finally:
            db.close()

    def get_risk_summary(self) -> dict[str, Any]:
        """Get risk assessment summary."""
        metrics = self.get_metrics(hours=24)
        return {
            "risk_distribution": metrics.risk_distribution,
            "hourly_distribution": metrics.hourly_distribution,
            "period": "24h",
            "generated_at": datetime.utcnow().isoformat(),
        }

    def get_daily_revenue(self, days: int = 30) -> dict[str, Any]:
        """Get daily revenue trend."""
        db = self._get_db()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            entries = (
                db.query(AuditLog)
                .filter(AuditLog.event_type == "checkout_approved", AuditLog.created_at >= cutoff)
                .order_by(AuditLog.created_at.asc())
                .all()
            )

            daily: dict[str, float] = {}
            for entry in entries:
                day = entry.created_at.strftime("%Y-%m-%d")
                data = json.loads(entry.details) if entry.details else {}
                details = data.get("details", data) if isinstance(data, dict) else {}
                amount = float(details.get("amount", 0))
                daily[day] = daily.get(day, 0) + amount

            return {
                "daily_revenue": {k: round(v, 2) for k, v in daily.items()},
                "days": days,
                "total": round(sum(daily.values()), 2),
                "generated_at": datetime.utcnow().isoformat(),
            }
        finally:
            db.close()

    def get_revenue_summary(self) -> dict[str, Any]:
        db = self._get_db()
        try:
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = now - timedelta(days=now.weekday())
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            def sum_revenue(start_time: datetime) -> float:
                result = db.query(AuditLog).filter(
                    AuditLog.event_type == "checkout_approved",
                    AuditLog.created_at >= start_time,
                ).all()
                total = 0.0
                for o in result:
                    if not o.details:
                        continue
                    data = json.loads(o.details)
                    details = data.get("details", data) if isinstance(data, dict) else {}
                    total += float(details.get("amount", 0))
                return total

            return {
                "today": round(sum_revenue(today_start), 2),
                "this_week": round(sum_revenue(week_start), 2),
                "this_month": round(sum_revenue(month_start), 2),
                "generated_at": now.isoformat(),
            }
        finally:
            db.close()

    def get_failure_analysis(self) -> dict[str, Any]:
        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=24)
            failures = db.query(AuditLog).filter(
                AuditLog.created_at >= cutoff,
            ).filter(
                AuditLog.event_type.in_(["payment_declined", "checkout_blocked"])
            ).all()

            reasons: dict[str, int] = {}
            for f in failures:
                details = json.loads(f.details) if f.details else {}
                reason = details.get("reason", "Unknown")
                if "limit" in reason.lower():
                    category = "Session Limit"
                elif "category" in reason.lower():
                    category = "Category Restriction"
                elif "declined" in reason.lower():
                    category = "Payment Declined"
                else:
                    category = "Other"
                reasons[category] = reasons.get(category, 0) + 1

            return {
                "total_failures": len(failures),
                "reasons": reasons,
                "period_hours": 24,
            }
        finally:
            db.close()


payment_analytics = PaymentAnalytics()
