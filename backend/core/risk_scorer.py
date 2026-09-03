from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

from backend.db.models import AgentAction
from backend.db.session import SessionLocal


@dataclass
class RiskFactor:
    """Individual risk factor contributing to the overall score."""
    name: str
    impact: float  # -1.0 to 1.0, negative is good (reduces risk)
    description: str


@dataclass
class RiskAssessment:
    """Complete risk assessment for a transaction."""
    risk_score: float  # 0.0 to 1.0
    risk_level: str  # "low", "medium", "high", "critical"
    factors: list[RiskFactor] = field(default_factory=list)
    recommendation: str = ""
    requires_manual_review: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_score": round(self.risk_score, 2),
            "risk_level": self.risk_level,
            "factors": [
                {
                    "factor": f.name,
                    "impact": f.impact,
                    "description": f.description,
                }
                for f in self.factors
            ],
            "recommendation": self.recommendation,
            "requires_manual_review": self.requires_manual_review,
        }


class TransactionRiskScorer:
    """Analyzes transaction risk before payment processing."""

    # Risk thresholds
    LOW_RISK_THRESHOLD = 0.3
    MEDIUM_RISK_THRESHOLD = 0.6
    HIGH_RISK_THRESHOLD = 0.8

    # Velocity limits
    MAX_TRANSACTIONS_PER_MINUTE = 5
    MAX_TRANSACTIONS_PER_HOUR = 20
    MAX_AMOUNT_PER_HOUR = 50000  # ₹50,000

    def __init__(self) -> None:
        self._recent_transactions: list[dict[str, Any]] = []

    def assess_transaction(
        self,
        amount: float,
        category: str,
        session_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> RiskAssessment:
        """Perform comprehensive risk assessment for a transaction."""
        factors: list[RiskFactor] = []
        score = 0.0

        # Factor 1: Amount risk
        amount_factor = self._assess_amount_risk(amount)
        factors.append(amount_factor)
        score += amount_factor.impact

        # Factor 2: Category risk
        category_factor = self._assess_category_risk(category)
        factors.append(category_factor)
        score += category_factor.impact

        # Factor 3: Velocity risk
        velocity_factor = self._assess_velocity_risk(amount, session_id)
        factors.append(velocity_factor)
        score += velocity_factor.impact

        # Factor 4: Session history risk
        history_factor = self._assess_session_history(session_id)
        factors.append(history_factor)
        score += history_factor.impact

        # Factor 5: Device/IP risk
        device_factor = self._assess_device_risk(user_agent, ip_address)
        factors.append(device_factor)
        score += device_factor.impact

        # Normalize score to 0-1 range
        score = max(0.0, min(1.0, score))

        # Determine risk level
        risk_level = self._get_risk_level(score)

        # Generate recommendation
        recommendation = self._get_recommendation(score, factors)

        # Determine if manual review required
        requires_manual_review = score >= self.HIGH_RISK_THRESHOLD

        return RiskAssessment(
            risk_score=score,
            risk_level=risk_level,
            factors=factors,
            recommendation=recommendation,
            requires_manual_review=requires_manual_review,
        )

    def _assess_amount_risk(self, amount: float) -> RiskFactor:
        """Assess risk based on transaction amount."""
        if amount <= 500:
            return RiskFactor(
                name="low_amount",
                impact=-0.1,
                description="Low-value transaction (₹500 or less)",
            )
        elif amount <= 2000:
            return RiskFactor(
                name="medium_amount",
                impact=0.0,
                description="Medium-value transaction (₹501-2000)",
            )
        elif amount <= 5000:
            return RiskFactor(
                name="high_amount",
                impact=0.15,
                description="High-value transaction (₹2001-5000)",
            )
        else:
            return RiskFactor(
                name="very_high_amount",
                impact=0.25,
                description="Very high-value transaction (₹5000+)",
            )

    def _assess_category_risk(self, category: str) -> RiskFactor:
        """Assess risk based on product category."""
        high_risk_categories = {"sets", "wellness"}
        medium_risk_categories = {"makeup", "skincare"}
        low_risk_categories = {"moisturizer", "sunscreen", "serum", "cleanser", "face oil"}

        category_lower = category.lower()

        if category_lower in low_risk_categories:
            return RiskFactor(
                name="low_risk_category",
                impact=-0.05,
                description=f"Category '{category}' is low-risk",
            )
        elif category_lower in medium_risk_categories:
            return RiskFactor(
                name="medium_risk_category",
                impact=0.05,
                description=f"Category '{category}' is medium-risk",
            )
        elif category_lower in high_risk_categories:
            return RiskFactor(
                name="high_risk_category",
                impact=0.1,
                description=f"Category '{category}' is high-risk",
            )
        else:
            return RiskFactor(
                name="unknown_category",
                impact=0.2,
                description=f"Unknown category '{category}'",
            )

    def _assess_velocity_risk(self, amount: float, session_id: Optional[str]) -> RiskFactor:
        """Assess risk based on transaction velocity."""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            one_minute_ago = now - timedelta(minutes=1)
            one_hour_ago = now - timedelta(hours=1)

            # Count recent transactions
            recent_minute_count = (
                db.query(AgentAction)
                .filter(
                    AgentAction.created_at >= one_minute_ago,
                    AgentAction.action_type.in_(["CHECKOUT_APPROVED", "PAYMENT_DECLINED"]),
                )
                .count()
            )

            recent_hour_count = (
                db.query(AgentAction)
                .filter(
                    AgentAction.created_at >= one_hour_ago,
                    AgentAction.action_type.in_(["CHECKOUT_APPROVED", "PAYMENT_DECLINED"]),
                )
                .count()
            )

            # Sum recent amounts
            recent_hour_amount = (
                db.query(AgentAction)
                .filter(
                    AgentAction.created_at >= one_hour_ago,
                    AgentAction.action_type == "CHECKOUT_APPROVED",
                )
                .all()
            )
            hour_total = sum(float(a.amount or 0) for a in recent_hour_amount)

            if recent_minute_count >= self.MAX_TRANSACTIONS_PER_MINUTE:
                return RiskFactor(
                    name="velocity_minute_exceeded",
                    impact=0.3,
                    description=f"Exceeded {self.MAX_TRANSACTIONS_PER_MINUTE} transactions/minute",
                )
            elif recent_hour_count >= self.MAX_TRANSACTIONS_PER_HOUR:
                return RiskFactor(
                    name="velocity_hour_exceeded",
                    impact=0.25,
                    description=f"Exceeded {self.MAX_TRANSACTIONS_PER_HOUR} transactions/hour",
                )
            elif hour_total + amount > self.MAX_AMOUNT_PER_HOUR:
                return RiskFactor(
                    name="hourly_amount_exceeded",
                    impact=0.2,
                    description=f"Hourly amount would exceed ₹{self.MAX_AMOUNT_PER_HOUR}",
                )
            elif recent_minute_count >= 3:
                return RiskFactor(
                    name="velocity_warning",
                    impact=0.1,
                    description="High transaction frequency detected",
                )
            else:
                return RiskFactor(
                    name="velocity_normal",
                    impact=-0.05,
                    description="Transaction velocity within normal limits",
                )
        finally:
            db.close()

    def _assess_session_history(self, session_id: Optional[str]) -> RiskFactor:
        """Assess risk based on session history."""
        db = SessionLocal()
        try:
            # Count total successful transactions
            success_count = (
                db.query(AgentAction)
                .filter(AgentAction.action_type == "CHECKOUT_APPROVED")
                .count()
            )

            # Count blocked transactions
            blocked_count = (
                db.query(AgentAction)
                .filter(AgentAction.action_type == "BOUNDS_REJECTED")
                .count()
            )

            # Count declined payments
            declined_count = (
                db.query(AgentAction)
                .filter(AgentAction.action_type == "PAYMENT_DECLINED")
                .count()
            )

            total_attempts = success_count + blocked_count + declined_count

            if total_attempts == 0:
                return RiskFactor(
                    name="new_session",
                    impact=0.05,
                    description="New session with no history",
                )

            decline_rate = declined_count / total_attempts if total_attempts > 0 else 0
            block_rate = blocked_count / total_attempts if total_attempts > 0 else 0

            if decline_rate > 0.5:
                return RiskFactor(
                    name="high_decline_rate",
                    impact=0.3,
                    description=f"High decline rate: {decline_rate:.0%}",
                )
            elif block_rate > 0.5:
                return RiskFactor(
                    name="high_block_rate",
                    impact=0.2,
                    description=f"High block rate: {block_rate:.0%}",
                )
            elif success_count > 10:
                return RiskFactor(
                    name="established_session",
                    impact=-0.1,
                    description="Established session with good history",
                )
            else:
                return RiskFactor(
                    name="normal_session",
                    impact=0.0,
                    description="Session history within normal limits",
                )
        finally:
            db.close()

    def _assess_device_risk(self, user_agent: Optional[str], ip_address: Optional[str]) -> RiskFactor:
        """Assess risk based on device/IP signals."""
        if not user_agent:
            return RiskFactor(
                name="missing_user_agent",
                impact=0.15,
                description="No user agent provided",
            )

        # Check for bot indicators
        bot_indicators = ["bot", "crawler", "spider", "scrape", "curl", "wget", "python-requests"]
        if any(indicator in user_agent.lower() for indicator in bot_indicators):
            return RiskFactor(
                name="bot_detected",
                impact=0.35,
                description="Automated tool/bot detected",
            )

        # Check for missing IP
        if not ip_address:
            return RiskFactor(
                name="missing_ip",
                impact=0.1,
                description="No IP address provided",
            )

        return RiskFactor(
            name="device_normal",
            impact=-0.05,
            description="Device signals appear normal",
        )

    def _get_risk_level(self, score: float) -> str:
        """Convert numeric score to risk level."""
        if score <= self.LOW_RISK_THRESHOLD:
            return "low"
        elif score <= self.MEDIUM_RISK_THRESHOLD:
            return "medium"
        elif score <= self.HIGH_RISK_THRESHOLD:
            return "high"
        else:
            return "critical"

    def _get_recommendation(self, score: float, factors: list[RiskFactor]) -> str:
        """Generate recommendation based on risk assessment."""
        if score <= self.LOW_RISK_THRESHOLD:
            return "Transaction appears safe. Proceed with payment."
        elif score <= self.MEDIUM_RISK_THRESHOLD:
            return "Transaction has moderate risk. Consider additional verification."
        elif score <= self.HIGH_RISK_THRESHOLD:
            return "High-risk transaction. Manual review recommended before proceeding."
        else:
            return "Critical risk level. Transaction should be blocked pending review."


# Singleton instance
risk_scorer = TransactionRiskScorer()
