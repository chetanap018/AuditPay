from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.audit_trail import audit_trail
from backend.core.campaigns import campaign_orchestrator
from backend.core.guardrails import (
    check_order_bounds,
    check_session_order_limit,
)
from backend.core.idempotency import idempotency_manager
from backend.core.razorpay_client import get_client
from backend.core.risk_scorer import risk_scorer
from backend.db.models import AgentAction, Order, Product
from backend.db.session import get_db

router = APIRouter(prefix="/checkout", tags=["checkout"])


class CheckoutRequest(BaseModel):
    product_id: int
    amount: float
    session_id: Optional[str] = None
    simulate_failure: bool = False
    idempotency_key: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class CheckoutResponse(BaseModel):
    success: bool
    status: str
    message: str
    reasoning: str
    bounds_passed: bool
    payment_url: Optional[str] = None
    retry_available: bool = False
    original_amount: Optional[float] = None
    discount_percent: Optional[float] = None
    discount_amount: Optional[float] = None
    final_amount: Optional[float] = None
    applied_campaign: Optional[dict] = None
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    risk_factors: list[str] = []
    idempotency_key: Optional[str] = None
    is_duplicate: bool = False


@router.post("", response_model=CheckoutResponse)
def create_checkout(payload: CheckoutRequest, db: Session = Depends(get_db)) -> CheckoutResponse:
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    # ===== IDEMPOTENCY CHECK =====
    if payload.idempotency_key:
        # Validate key format
        is_valid, error_msg = idempotency_manager.validate_key_format(payload.idempotency_key)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Check for duplicate
        existing = idempotency_manager.check_idempotency(payload.idempotency_key)
        if existing:
            return CheckoutResponse(
                success=True,
                status="duplicate_request",
                message="This request was already processed. Returning cached result.",
                reasoning="Idempotency key was already used for an identical request.",
                bounds_passed=True,
                idempotency_key=payload.idempotency_key,
                is_duplicate=True,
            )

    # Calculate campaign discount
    price_info = campaign_orchestrator.calculate_product_price({
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "stock": product.stock,
        "category": product.category,
    })
    original_amount = price_info["original_price"]
    final_amount = price_info["discounted_price"]
    discount_percent = price_info["discount_percent"]
    discount_amount = price_info["savings"]
    applied_campaign = price_info["applied_offer"]

    # Use the discounted amount for checkout
    checkout_amount = final_amount

    # ===== RISK SCORING =====
    risk_assessment = risk_scorer.assess_transaction(
        amount=checkout_amount,
        category=product.category,
        session_id=payload.session_id,
        user_agent=payload.user_agent,
        ip_address=payload.ip_address,
    )

    # Block critical risk transactions
    risk_factor_names = [f.name for f in risk_assessment.factors]
    if risk_assessment.risk_level == "critical":
        db.add(
            AgentAction(
                action_type="RISK_BLOCKED",
                reasoning=f"Transaction blocked due to critical risk: {risk_assessment.recommendation}",
                amount=checkout_amount,
                bounds_passed=False,
                session_id=payload.session_id,
            )
        )
        audit_trail.add_entry(
            event_type="risk_blocked",
            details={
                "risk_score": risk_assessment.risk_score,
                "risk_level": risk_assessment.risk_level,
                "risk_factors": risk_factor_names,
                "recommendation": risk_assessment.recommendation,
                "product_id": product.id,
                "amount": checkout_amount,
            },
        )
        db.commit()
        return CheckoutResponse(
            success=False,
            status="blocked",
            message="Transaction blocked due to high risk.",
            reasoning=risk_assessment.recommendation,
            bounds_passed=False,
            retry_available=False,
            risk_level=risk_assessment.risk_level,
            risk_score=risk_assessment.risk_score,
            risk_factors=risk_factor_names,
        )

    # ===== GUARDRAILS CHECK =====
    # The trust boundary runs before any payment call: it validates the amount the
    # agent proposed (payload.amount) as well as the final charge after campaign
    # discounts, plus the per-session order count and aggregate spend caps.
    requested_bounds = check_order_bounds(payload.amount, product.category)
    charge_bounds = check_order_bounds(checkout_amount, product.category)

    approved_actions = (
        db.query(AgentAction)
        .filter(AgentAction.action_type == "CHECKOUT_APPROVED")
        .filter(
            AgentAction.session_id.is_(None)
            if payload.session_id is None
            else AgentAction.session_id == payload.session_id
        )
        .all()
    )
    order_count = len(approved_actions)
    current_total = sum(float(action.amount or 0) for action in approved_actions)
    session_limit = check_session_order_limit(
        order_count=order_count,
        current_total=current_total,
        new_amount=checkout_amount,
    )

    if not requested_bounds.passed:
        reason = requested_bounds.reason
    elif not charge_bounds.passed:
        reason = charge_bounds.reason
    elif not session_limit.passed:
        reason = session_limit.reason
    else:
        reason = None

    if reason is not None:
        # Record the amount that was actually rejected: the agent's proposed amount
        # when the per-order bounds failed, otherwise the final charge amount.
        rejected_amount = payload.amount if not requested_bounds.passed else checkout_amount
        db.add(
            AgentAction(
                action_type="BOUNDS_REJECTED",
                reasoning=reason,
                amount=rejected_amount,
                bounds_passed=False,
                session_id=payload.session_id,
                risk_score=risk_assessment.risk_score,
                risk_factors=json.dumps(risk_factor_names),
            )
        )
        audit_trail.add_entry(
            event_type="checkout_blocked",
            details={
                "reason": reason,
                "product_id": product.id,
                "amount": checkout_amount,
                "risk_score": risk_assessment.risk_score,
                "risk_level": risk_assessment.risk_level,
                "risk_factors": risk_factor_names,
            },
        )
        db.commit()
        return CheckoutResponse(
            success=False,
            status="blocked",
            message="I stopped this checkout before it reached Razorpay.",
            reasoning=reason,
            bounds_passed=False,
            retry_available=False,
            original_amount=original_amount,
            discount_percent=discount_percent,
            discount_amount=discount_amount,
            final_amount=final_amount,
            applied_campaign=applied_campaign,
            risk_level=risk_assessment.risk_level,
            risk_score=risk_assessment.risk_score,
            risk_factors=risk_factor_names,
        )

    if payload.simulate_failure:
        reason = "Razorpay test payment was intentionally declined. No funds were captured and the order remains safe to retry."
        db.add(
            AgentAction(
                action_type="PAYMENT_DECLINED",
                reasoning=reason,
                amount=checkout_amount,
                bounds_passed=True,
                session_id=payload.session_id,
                risk_score=risk_assessment.risk_score,
                risk_factors=json.dumps(risk_factor_names),
            )
        )
        audit_trail.add_entry(
            event_type="payment_declined",
            details={
                "product_id": product.id,
                "amount": checkout_amount,
                "reason": reason,
                "risk_score": risk_assessment.risk_score,
                "risk_level": risk_assessment.risk_level,
            },
        )
        db.commit()
        return CheckoutResponse(
            success=False,
            status="payment_declined",
            message="The test payment was declined — your money is safe. You can retry with a different test payment method.",
            reasoning=reason,
            bounds_passed=True,
            retry_available=True,
            original_amount=original_amount,
            discount_percent=discount_percent,
            discount_amount=discount_amount,
            final_amount=final_amount,
            applied_campaign=applied_campaign,
            risk_level=risk_assessment.risk_level,
            risk_score=risk_assessment.risk_score,
            risk_factors=risk_factor_names,
        )

    try:
        client = get_client()
        order = client.order.create(
            {
                "amount": int(checkout_amount * 100),
                "currency": "INR",
                "payment_capture": 1,
                "notes": {"product_id": str(product.id), "product_name": product.name},
            }
        )
    except RuntimeError:
        db.add(
            AgentAction(
                action_type="CHECKOUT_APPROVED",
                reasoning=(
                    f"Guardrails passed: ₹{checkout_amount} is within the maximum and category ‘{product.category}’ is approved. "
                    f"Razorpay credentials are not configured yet, so the test checkout is mocked."
                ),
                amount=checkout_amount,
                bounds_passed=True,
                session_id=payload.session_id,
            )
        )
        db.add(
            Order(
                product_id=product.id,
                amount=checkout_amount,
                total=checkout_amount,
                status="created_mocked",
                idempotency_key=payload.idempotency_key,
                risk_score=risk_assessment.risk_score,
                risk_factors=json.dumps(risk_factor_names),
            )
        )
        audit_trail.add_entry(
            event_type="checkout_mocked",
            details={
                "product_id": product.id,
                "amount": checkout_amount,
                "status": "mocked",
                "risk_score": risk_assessment.risk_score,
                "risk_level": risk_assessment.risk_level,
            },
        )
        # Store idempotency key after successful processing
        if payload.idempotency_key:
            idempotency_manager.store_idempotency_response(
                idempotency_key=payload.idempotency_key,
                status_code=200,
                response_body={"order_id": None, "amount": checkout_amount, "mocked": True},
            )

        db.commit()
        return CheckoutResponse(
            success=True,
            status="checkout_created",
            message="Checkout is ready. Razorpay keys are not configured yet, so this is running in safe mock mode.",
            reasoning=(
                f"Guardrails passed: ₹{checkout_amount} is within the maximum and category ‘{product.category}’ is approved. "
                "A real Razorpay order cannot be created until the environment variables are set."
            ),
            bounds_passed=True,
            payment_url=None,
            retry_available=False,
            original_amount=original_amount,
            discount_percent=discount_percent,
            discount_amount=discount_amount,
            final_amount=final_amount,
            applied_campaign=applied_campaign,
            risk_level=risk_assessment.risk_level,
            risk_score=risk_assessment.risk_score,
            risk_factors=risk_factor_names,
        )

    db.add(
        AgentAction(
            action_type="CHECKOUT_APPROVED",
            reasoning=(
                f"Guardrails passed: ₹{checkout_amount} is under the maximum and category ‘{product.category}’ is approved. "
                f"Created a Razorpay test checkout for {product.name}."
            ),
            amount=checkout_amount,
            bounds_passed=True,
            session_id=payload.session_id,
        )
    )
    db.add(
        Order(
            product_id=product.id,
            amount=checkout_amount,
            total=checkout_amount,
            status="created",
            razorpay_order_id=order.get("id"),
            idempotency_key=payload.idempotency_key,
            risk_score=risk_assessment.risk_score,
            risk_factors=json.dumps(risk_factor_names),
        )
    )
    audit_trail.add_entry(
        event_type="checkout_approved",
        details={
            "product_id": product.id,
            "amount": checkout_amount,
            "razorpay_order_id": order.get("id"),
            "risk_score": risk_assessment.risk_score,
            "risk_level": risk_assessment.risk_level,
            "risk_factors": risk_factor_names,
        },
    )

    # Store idempotency key after successful processing
    if payload.idempotency_key:
        idempotency_manager.store_idempotency_response(
            idempotency_key=payload.idempotency_key,
            status_code=200,
            response_body={"order_id": order.get("id"), "amount": checkout_amount},
        )

    db.commit()
    return CheckoutResponse(
        success=True,
        status="checkout_created",
        message="Checkout is ready. This is a Razorpay test-mode payment link.",
        reasoning=(
            f"Guardrails passed: ₹{checkout_amount} is under the maximum and category ‘{product.category}’ is approved. "
            f"Created a Razorpay test checkout for {product.name}."
        ),
        bounds_passed=True,
        payment_url=None,
        retry_available=False,
        original_amount=original_amount,
        discount_percent=discount_percent,
        discount_amount=discount_amount,
        final_amount=final_amount,
        applied_campaign=applied_campaign,
        risk_level=risk_assessment.risk_level,
        risk_score=risk_assessment.risk_score,
        risk_factors=risk_factor_names,
        idempotency_key=payload.idempotency_key,
    )
