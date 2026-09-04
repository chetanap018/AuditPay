from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.guardrails import MAX_SESSION_TOTAL_VALUE
from backend.core.audit_trail import audit_trail
from backend.db.models import AgentAction, AuditLog
from backend.db.session import get_db

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditEvent(BaseModel):
    id: int
    action_type: str
    reasoning: str
    amount: Optional[float] = None
    bounds_passed: bool
    candidates_considered: Optional[list[dict[str, Any]]] = None
    outcome: Optional[str] = None
    timestamp: str


class AuditSummary(BaseModel):
    actions_today: int
    orders_approved: int
    total_value: float
    session_total_spend: float
    session_total_cap: float
    session_remaining: float
    guardrail_pass_rate: float
    failed_payments: int


@router.get("/log", response_model=list[AuditEvent])
def get_audit_log(db: Session = Depends(get_db)) -> list[AuditEvent]:
    events = db.query(AgentAction).order_by(AgentAction.created_at.desc()).all()
    result: list[AuditEvent] = []
    for event in events:
        candidates = None
        if event.candidates_considered:
            try:
                parsed = json.loads(event.candidates_considered)
                candidates = parsed if isinstance(parsed, list) else None
            except json.JSONDecodeError:
                candidates = None

        result.append(
            AuditEvent(
                id=event.id,
                action_type=event.action_type,
                reasoning=event.reasoning,
                amount=event.amount,
                bounds_passed=event.bounds_passed,
                candidates_considered=candidates,
                outcome="Completed" if event.bounds_passed else "Blocked",
                timestamp=event.created_at.isoformat(),
            )
        )
    return result


@router.get("/summary", response_model=AuditSummary)
def get_audit_summary(db: Session = Depends(get_db)) -> AuditSummary:
    actions = db.query(AgentAction).all()
    approved = sum(1 for item in actions if item.action_type == "CHECKOUT_APPROVED")
    total_value = sum(float(item.amount or 0) for item in actions if item.amount is not None)
    session_total_spend = sum(
        float(item.amount or 0)
        for item in actions
        if item.action_type == "CHECKOUT_APPROVED" and item.amount is not None
    )
    failed_payments = sum(1 for item in actions if item.action_type == "PAYMENT_DECLINED")
    guardrail_pass_rate = (
        (sum(1 for item in actions if item.bounds_passed) / len(actions)) * 100 if actions else 100.0
    )
    session_remaining = max(0.0, MAX_SESSION_TOTAL_VALUE - session_total_spend)
    return AuditSummary(
        actions_today=len(actions),
        orders_approved=approved,
        total_value=total_value,
        session_total_spend=session_total_spend,
        session_total_cap=MAX_SESSION_TOTAL_VALUE,
        session_remaining=session_remaining,
        guardrail_pass_rate=round(guardrail_pass_rate, 2),
        failed_payments=failed_payments,
    )


@router.get("/logs")
def get_json_audit_log(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    events = db.query(AuditLog).order_by(AuditLog.created_at.desc()).all()
    result: list[dict[str, Any]] = []
    for event in events:
        try:
            payload = json.loads(event.details)
        except json.JSONDecodeError:
            payload = {"details": event.details}
        result.append({
            "id": event.id,
            "event_type": event.event_type,
            "details": payload,
            "timestamp": event.created_at.isoformat(),
        })
    return result
