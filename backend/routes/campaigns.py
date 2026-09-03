from __future__ import annotations

from fastapi import APIRouter

from backend.core.campaigns import campaign_orchestrator

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("")
def get_active_campaigns() -> dict:
    """Get all active campaigns, bundles, and offers."""
    return campaign_orchestrator.get_campaign_summary()


@router.get("/bundles")
def get_bundles() -> list[dict]:
    """Get all active bundle deals."""
    bundles = campaign_orchestrator.get_active_bundles()
    return [
        {
            "id": b.id,
            "name": b.name,
            "description": b.description,
            "product_ids": b.product_ids,
            "original_price": b.original_price,
            "bundle_price": b.bundle_price,
            "savings": b.savings,
            "discount_percent": b.discount_percent,
        }
        for b in bundles
    ]


@router.get("/offers")
def get_offers() -> list[dict]:
    """Get all currently active time-based offers."""
    offers = [o for o in campaign_orchestrator.offers if o.is_currently_active()]
    return [
        {
            "id": o.id,
            "name": o.name,
            "description": o.description,
            "discount_percent": o.discount_percent,
            "category": o.category,
            "product_ids": o.product_ids,
        }
        for o in offers
    ]


@router.post("/calculate-price")
def calculate_price(product: dict) -> dict:
    """Calculate the final price for a product after applying best offer."""
    return campaign_orchestrator.calculate_product_price(product)


@router.post("/calculate-cart-discount")
def calculate_cart_discount(cart_info: dict) -> dict:
    """Calculate additional discount based on cart conditions."""
    item_count = cart_info.get("item_count", 0)
    cart_total = cart_info.get("cart_total", 0.0)
    return campaign_orchestrator.calculate_cart_discount(item_count, cart_total)
