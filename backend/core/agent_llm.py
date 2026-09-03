from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# Product relationships for upsell/cross-sell
# Format: category -> {upsell: [better categories], cross_sell: [complementary categories]}
CATEGORY_RELATIONSHIPS: dict[str, dict[str, list[str]]] = {
    "cleanser": {
        "upsell": ["serum", "face oil"],
        "cross_sell": ["moisturizer", "sunscreen"],
    },
    "moisturizer": {
        "upsell": ["face oil", "serum"],
        "cross_sell": ["cleanser", "sunscreen"],
    },
    "serum": {
        "upsell": ["face oil", "sets"],
        "cross_sell": ["cleanser", "moisturizer"],
    },
    "sunscreen": {
        "upsell": ["sets", "skincare"],
        "cross_sell": ["cleanser", "moisturizer"],
    },
    "face oil": {
        "upsell": ["sets"],
        "cross_sell": ["cleanser", "serum"],
    },
    "sets": {
        "upsell": [],
        "cross_sell": ["sunscreen", "skincare"],
    },
    "makeup": {
        "upsell": ["sets", "skincare"],
        "cross_sell": ["cleanser", "moisturizer"],
    },
    "skincare": {
        "upsell": ["sets"],
        "cross_sell": ["cleanser", "moisturizer", "sunscreen"],
    },
    "wellness": {
        "upsell": ["sets"],
        "cross_sell": ["moisturizer", "skincare"],
    },
}


@dataclass
class AgentDecision:
    message: str
    reasoning: str
    product_id: Optional[int] = None
    amount: Optional[float] = None
    guardrail_status: str = "pending"
    candidates_considered: list[dict[str, str | float | int]] = field(default_factory=list)
    # Upsell/Cross-sell fields
    upsell_product: Optional[dict[str, Any]] = None
    cross_sell_products: list[dict[str, Any]] = field(default_factory=list)
    bundle_offer: Optional[dict[str, Any]] = None


class AgentLLM:
    """Thin abstraction around the model/provider. Easy to swap providers."""

    def __init__(self, model: str = "demo-model") -> None:
        self.model = model

    def decide(self, user_message: str, catalog: list[dict[str, Any]]) -> AgentDecision:
        normalized = user_message.lower()
        best_match = None
        considered: list[dict[str, str | float | int]] = []

        for item in catalog:
            item_category = str(item.get("category", "")).lower()
            if "moisturizer" in normalized and item_category != "moisturizer":
                reason = "wrong category"
            elif "sunscreen" in normalized and item_category != "sunscreen":
                reason = "wrong category"
            elif "serum" in normalized and item_category != "serum":
                reason = "wrong category"
            elif "dry skin" in normalized and item_category not in {"moisturizer", "face oil", "serum"}:
                reason = "wrong category"
            elif item.get("stock", 0) <= 0:
                reason = "out of stock"
            elif item.get("price", 0) > 8000:
                reason = "over budget"
            else:
                reason = "less suitable match"

            if item.get("stock", 0) <= 0 or item.get("price", 0) > 8000:
                considered.append({
                    "name": str(item.get("name", "Unknown product")),
                    "category": str(item.get("category", "unknown")),
                    "price": float(item.get("price", 0)),
                    "reason": reason,
                })

        for item in catalog:
            item_category = str(item.get("category", "")).lower()
            if "moisturizer" in normalized and item_category != "moisturizer":
                continue
            if "sunscreen" in normalized and item_category != "sunscreen":
                continue
            if "serum" in normalized and item_category != "serum":
                continue
            if "dry skin" in normalized and item_category not in {"moisturizer", "face oil", "serum"}:
                continue
            if item.get("stock", 0) <= 0:
                continue

            if best_match is None or item["price"] < best_match["price"]:
                best_match = item

        if best_match is None:
            fallback = catalog[0]
            if len(catalog) > 1:
                for other in catalog[1:3]:
                    considered.append({
                        "name": str(other.get("name", "Unknown product")),
                        "category": str(other.get("category", "unknown")),
                        "price": float(other.get("price", 0)),
                        "reason": "less suitable match",
                    })
            return AgentDecision(
                message="I could not find an exact match, but I found a safe starter product to review.",
                reasoning=(
                    f"No category/price match was identified, so I selected {fallback['name']} because it is in stock and allowed by the catalog guardrails."
                ),
                product_id=fallback["id"],
                amount=float(fallback["price"]),
                guardrail_status="passed",
                candidates_considered=considered[:3],
            )

        candidate_budget = float(best_match["price"])
        for item in catalog:
            if item.get("id") == best_match.get("id"):
                continue
            if len(considered) >= 3:
                break
            if item.get("stock", 0) <= 0:
                reason = "out of stock"
            elif "moisturizer" in normalized and str(item.get("category", "")).lower() != "moisturizer":
                reason = "wrong category"
            elif "sunscreen" in normalized and str(item.get("category", "")).lower() != "sunscreen":
                reason = "wrong category"
            elif "serum" in normalized and str(item.get("category", "")).lower() != "serum":
                reason = "wrong category"
            elif "dry skin" in normalized and str(item.get("category", "")).lower() not in {"moisturizer", "face oil", "serum"}:
                reason = "wrong category"
            elif float(item.get("price", 0)) > float(best_match.get("price", 0)):
                reason = "over budget"
            else:
                reason = "less suitable match"
            considered.append({
                "name": str(item.get("name", "Unknown product")),
                "category": str(item.get("category", "unknown")),
                "price": float(item.get("price", 0)),
                "reason": reason,
            })

        return AgentDecision(
            message=f"I found {best_match['name']} for ₹{best_match['price']}. I recommend buying it because it matches your request and stays within the allow-listed category.",
            reasoning=(
                f"selected {best_match['name']} because price ₹{candidate_budget} matches the request and category '{best_match['category']}' is approved for purchase."
            ),
            product_id=best_match["id"],
            amount=candidate_budget,
            guardrail_status="passed",
            candidates_considered=considered[:3],
            upsell_product=self._find_upsell(best_match, catalog),
            cross_sell_products=self._find_cross_sells(best_match, catalog),
        )

    def _find_upsell(self, product: dict[str, Any], catalog: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
        """Find a better/more expensive product in a related category."""
        category = str(product.get("category", "")).lower()
        price = float(product.get("price", 0))
        relationships = CATEGORY_RELATIONSHIPS.get(category, {})
        upsell_categories = relationships.get("upsell", [])

        for upsell_cat in upsell_categories:
            for item in catalog:
                item_category = str(item.get("category", "")).lower()
                item_price = float(item.get("price", 0))
                item_stock = int(item.get("stock", 0))
                if item_category == upsell_cat and item_price > price and item_stock > 0:
                    return {
                        "id": item["id"],
                        "name": item["name"],
                        "category": item["category"],
                        "price": item_price,
                        "reason": f"Upgrade to {upsell_cat} for better results",
                    }
        return None

    def _find_cross_sells(self, product: dict[str, Any], catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Find complementary products from different categories."""
        category = str(product.get("category", "")).lower()
        product_id = product.get("id")
        relationships = CATEGORY_RELATIONSHIPS.get(category, {})
        cross_sell_categories = relationships.get("cross_sell", [])
        cross_sells: list[dict[str, Any]] = []

        for cross_cat in cross_sell_categories:
            for item in catalog:
                item_category = str(item.get("category", "")).lower()
                item_stock = int(item.get("stock", 0))
                if item_category == cross_cat and item_stock > 0 and item.get("id") != product_id:
                    cross_sells.append({
                        "id": item["id"],
                        "name": item["name"],
                        "category": item["category"],
                        "price": float(item.get("price", 0)),
                        "reason": f"Pairs well with {product['name']}",
                    })
                    break  # One product per category

        return cross_sells[:2]  # Max 2 cross-sell suggestions
