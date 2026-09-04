from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException  # type: ignore[import-not-found]
from pydantic import BaseModel  # type: ignore[import-not-found]
from sqlalchemy.orm import Session  # type: ignore[import-not-found]

from backend.core.agent_llm import AgentLLM
from backend.core.agent_tools import search_catalog
from backend.core.campaigns import campaign_orchestrator
from backend.db.models import AgentAction, Product
from backend.db.session import get_db

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    message: str
    status: str
    reasoning: str
    guardrail_status: str
    proposed_amount: Optional[float] = None
    product_id: Optional[int] = None
    # Upsell/Cross-sell fields
    upsell_product: Optional[dict] = None
    cross_sell_products: list[dict] = []
    bundle_offer: Optional[dict] = None


@router.post("", response_model=AgentResponse)
def handle_agent_request(payload: AgentRequest, db: Session = Depends(get_db)) -> AgentResponse:
    products = db.query(Product).all()
    catalog = [
        {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "price": item.price,
            "stock": item.stock,
            "category": item.category,
        }
        for item in products
    ]

    filtered = search_catalog(catalog, payload.message)
    llm = AgentLLM()
    decision = llm.decide(payload.message, filtered or catalog)

    if decision.product_id is None:
        raise HTTPException(status_code=400, detail="No safe product was identified.")

    # Check for bundle offers
    bundle_offer = None
    if decision.cross_sell_products:
        bundle_product_ids = [decision.product_id] + [p["id"] for p in decision.cross_sell_products]
        bundle = campaign_orchestrator.get_bundle_for_products(bundle_product_ids)
        if bundle:
            bundle_offer = {
                "id": bundle.id,
                "name": bundle.name,
                "description": bundle.description,
                "original_price": bundle.original_price,
                "bundle_price": bundle.bundle_price,
                "savings": bundle.savings,
                "discount_percent": bundle.discount_percent,
            }

    db.add(
        AgentAction(
            action_type="RECOMMENDATION",
            reasoning=decision.reasoning,
            amount=decision.amount,
            bounds_passed=True,
            session_id=payload.session_id,
            candidates_considered=json.dumps(decision.candidates_considered or []),
        )
    )
    db.commit()

    return AgentResponse(
        message=decision.message,
        status="recommendation",
        reasoning=decision.reasoning,
        guardrail_status=decision.guardrail_status,
        proposed_amount=decision.amount,
        product_id=decision.product_id,
        upsell_product=decision.upsell_product,
        cross_sell_products=decision.cross_sell_products,
        bundle_offer=bundle_offer,
    )
