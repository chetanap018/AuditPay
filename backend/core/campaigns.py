from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional


@dataclass
class BundleDeal:
    """A bundle of products sold together at a discount."""
    id: str
    name: str
    description: str
    product_ids: list[int]
    original_price: float
    bundle_price: float
    is_active: bool = True

    @property
    def savings(self) -> float:
        return self.original_price - self.bundle_price

    @property
    def discount_percent(self) -> float:
        if self.original_price == 0:
            return 0
        return round((self.savings / self.original_price) * 100, 1)


@dataclass
class TimeBasedOffer:
    """A time-limited discount on specific categories or products."""
    id: str
    name: str
    description: str
    discount_percent: float
    category: Optional[str] = None
    product_ids: list[int] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(days=7))
    is_active: bool = True

    def is_currently_active(self) -> bool:
        now = datetime.utcnow()
        return self.is_active and self.start_time <= now <= self.end_time


@dataclass
class AutoDiscountRule:
    """Automatic discount rules based on inventory or cart conditions."""
    id: str
    name: str
    description: str
    condition_type: str
    condition_value: float
    discount_percent: float
    is_active: bool = True


class CampaignOrchestrator:
    """Manages promotional campaigns, bundles, and auto-discounts."""

    def __init__(self) -> None:
        self.bundles: list[BundleDeal] = []
        self.offers: list[TimeBasedOffer] = []
        self.auto_discounts: list[AutoDiscountRule] = []
        self._initialize_default_campaigns()

    def _initialize_default_campaigns(self) -> None:
        """Set up default campaigns for the skincare store."""
        self.bundles = [
            BundleDeal(
                id="starter-kit",
                name="Starter Skincare Kit",
                description="Cleanser + Moisturizer - Perfect for beginners",
                product_ids=[4, 1],
                original_price=1198,
                bundle_price=999,
            ),
            BundleDeal(
                id="complete-routine",
                name="Complete Routine Set",
                description="Cleanser + Serum + Moisturizer - Full skincare routine",
                product_ids=[4, 3, 1],
                original_price=2097,
                bundle_price=1799,
            ),
            BundleDeal(
                id="sun-protection",
                name="Sun Protection Duo",
                description="Sunscreen + Face Oil - Protect and nourish",
                product_ids=[2, 5],
                original_price=1739,
                bundle_price=1499,
            ),
        ]
        self.offers = [
            TimeBasedOffer(
                id="flash-serum",
                name="Flash Sale: Vitamin C Serum",
                description="20% off on Glowcore Vitamin C Serum - Today only!",
                discount_percent=20,
                product_ids=[3],
                end_time=datetime.utcnow() + timedelta(hours=24),
            ),
            TimeBasedOffer(
                id="weekend-skincare",
                name="Weekend Skincare Special",
                description="15% off on all skincare products",
                discount_percent=15,
                category="skincare",
                end_time=datetime.utcnow() + timedelta(days=2),
            ),
        ]
        self.auto_discounts = [
            AutoDiscountRule(
                id="low-stock-clearance",
                name="Low Stock Clearance",
                description="25% off when stock is below 10 units",
                condition_type="low_stock",
                condition_value=10,
                discount_percent=25,
            ),
            AutoDiscountRule(
                id="free-shipping",
                name="Free Shipping",
                description="10% off on orders above ₹1500",
                condition_type="cart_value",
                condition_value=1500,
                discount_percent=10,
            ),
            AutoDiscountRule(
                id="bulk-discount",
                name="Bulk Discount",
                description="15% off when buying 3 or more items",
                condition_type="item_count",
                condition_value=3,
                discount_percent=15,
            ),
        ]

    def get_active_bundles(self, product_ids: list[int] = None) -> list[BundleDeal]:
        """Get active bundles, optionally filtered by product IDs."""
        active = [b for b in self.bundles if b.is_active]
        if product_ids:
            active = [b for b in active if any(pid in b.product_ids for pid in product_ids)]
        return active

    def get_active_offers(self, product_id: int = None, category: str = None) -> list[TimeBasedOffer]:
        """Get currently active offers for a product or category."""
        return [
            o for o in self.offers
            if o.is_currently_active()
            and (product_id is None or product_id in o.product_ids or (category and o.category == category))
        ]

    def calculate_product_price(self, product: dict[str, Any]) -> dict[str, Any]:
        """Calculate the final price for a product after applying best offer."""
        original_price = float(product.get("price", 0))
        stock = int(product.get("stock", 0))
        category = str(product.get("category", ""))
        product_id = int(product.get("id", 0))

        best_discount = 0
        applied_offer = None

        for offer in self.get_active_offers(product_id, category):
            if offer.discount_percent > best_discount:
                best_discount = offer.discount_percent
                applied_offer = offer

        for rule in self.auto_discounts:
            if not rule.is_active:
                continue
            if rule.condition_type == "low_stock" and stock < rule.condition_value:
                if rule.discount_percent > best_discount:
                    best_discount = rule.discount_percent
                    applied_offer = rule

        discounted_price = round(original_price * (1 - best_discount / 100), 2)

        return {
            "original_price": original_price,
            "discounted_price": discounted_price,
            "discount_percent": best_discount,
            "savings": round(original_price - discounted_price, 2),
            "applied_offer": {
                "id": getattr(applied_offer, "id", None),
                "name": getattr(applied_offer, "name", None),
                "description": getattr(applied_offer, "description", None),
            } if applied_offer else None,
        }

    def calculate_cart_discount(self, item_count: int, cart_total: float) -> dict[str, Any]:
        """Calculate additional discount based on cart conditions."""
        best_discount = 0
        applied_rule = None

        for rule in self.auto_discounts:
            if not rule.is_active:
                continue
            if rule.condition_type == "cart_value" and cart_total >= rule.condition_value:
                if rule.discount_percent > best_discount:
                    best_discount = rule.discount_percent
                    applied_rule = rule
            elif rule.condition_type == "item_count" and item_count >= rule.condition_value:
                if rule.discount_percent > best_discount:
                    best_discount = rule.discount_percent
                    applied_rule = rule

        return {
            "discount_percent": best_discount,
            "discount_amount": round(cart_total * best_discount / 100, 2),
            "final_total": round(cart_total * (1 - best_discount / 100), 2),
            "applied_rule": {
                "id": getattr(applied_rule, "id", None),
                "name": getattr(applied_rule, "name", None),
                "description": getattr(applied_rule, "description", None),
            } if applied_rule else None,
        }

    def get_bundle_for_products(self, product_ids: list[int]) -> Optional[BundleDeal]:
        """Find a bundle that contains all the given products."""
        for bundle in self.get_active_bundles():
            if all(pid in bundle.product_ids for pid in product_ids):
                return bundle
        return None

    def get_campaign_summary(self) -> dict[str, Any]:
        """Get a summary of all active campaigns."""
        return {
            "active_bundles": len([b for b in self.bundles if b.is_active]),
            "active_offers": len([o for o in self.offers if o.is_currently_active()]),
            "auto_discounts": len([d for d in self.auto_discounts if d.is_active]),
            "bundles": [
                {
                    "id": b.id,
                    "name": b.name,
                    "description": b.description,
                    "original_price": b.original_price,
                    "bundle_price": b.bundle_price,
                    "savings": b.savings,
                    "discount_percent": b.discount_percent,
                }
                for b in self.bundles if b.is_active
            ],
            "offers": [
                {
                    "id": o.id,
                    "name": o.name,
                    "description": o.description,
                    "discount_percent": o.discount_percent,
                    "ends_in_hours": round((o.end_time - datetime.utcnow()).total_seconds() / 3600, 1),
                }
                for o in self.offers if o.is_currently_active()
            ],
        }


# Singleton instance
campaign_orchestrator = CampaignOrchestrator()
