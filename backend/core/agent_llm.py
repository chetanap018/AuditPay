from __future__ import annotations

import re
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

# Words that are pure conversation (greetings, small talk, acknowledgements).
GREETING_WORDS = {
    "hi", "hii", "hiii", "helo", "hello", "hey", "yo", "sup", "namaste",
    "thanks", "thank", "thx", "ty", "bye", "goodbye", "goodnight", "ok",
    "okay", "cool", "nice", "great", "awesome", "perfect", "lol", "haha",
    "hehe", "yes", "yeah", "yep", "no", "nope", "sure", "welcome", "done",
}

# Phrases that indicate conversation even when single words don't match.
CONVERSATIONAL_PHRASES = (
    "good morning", "good afternoon", "good evening", "good night",
    "thank you", "thanks a lot", "many thanks", "how are you",
    "who are you", "what can you do", "what's up", "whats up",
    "can you help", "nice to meet",
)

# Category nouns that explicitly name a product type.
TIER1_CATEGORY_KEYWORDS = {
    "moisturizer": ["moisturizer", "moisturiser"],
    "sunscreen": ["sunscreen", "sun cream", "suncare"],
    "serum": ["serum"],
    "cleanser": ["cleanser", "face wash"],
    "face oil": ["face oil", "facial oil"],
    "sets": ["set", "kit", "bundle", "duo"],
    "makeup": ["makeup", "make-up", "tint"],
    "skincare": ["skincare", "skin care", "mask"],
    "wellness": ["wellness", "supplement"],
}

# Descriptive words imply a category when no explicit noun was used.
TIER2_CATEGORY_KEYWORDS = {
    "moisturizer": ["hydrating", "hydration", "moisture", "cream", "lotion", "flaky", "dry skin"],
    "sunscreen": ["spf", "uv", "sun protection"],
    "serum": ["vitamin c", "brightening", "antioxidant"],
    "cleanser": ["cleanse", "foam"],
    "face oil": ["oil"],
    "sets": ["routine", "starter"],
    "skincare": ["dry skin", "tired skin", "stressed skin"],
}

# "Best sunscreen under ₹900" -> 900
BUDGET_PATTERN = re.compile(
    r"\b(?:under|below|less than|max(?:imum)?|upto|up to|within|cheaper than)\s*(?:₹|rs\.?|inr)?\s*(\d{1,6})\b"
)


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
        text = " ".join((user_message or "").lower().split())

        wanted = self._match_categories(text)
        budget = self._extract_budget(text)

        # Conversational turns (greetings, small talk) never propose a product.
        if self._is_conversational(text, wanted):
            return AgentDecision(
                message=(
                    "Hi! I'm the shopping agent for this store. I can recommend products and run a "
                    "guardrail-checked checkout for you. Ask for a moisturizer, sunscreen, serum, or "
                    "something for dry skin — every proposal is verified before any payment is attempted."
                ),
                reasoning="Conversational message with no purchase intent; no product proposal was made.",
                guardrail_status="not_applicable",
            )

        # Requests that match nothing in the catalog get an honest clarify reply,
        # never a random fallback product.
        if not wanted:
            available = sorted({str(item.get("category", "")) for item in catalog if item.get("stock", 0) > 0})
            listing = ", ".join(available) if available else "(the catalog is currently empty)"
            return AgentDecision(
                message=(
                    f"I couldn't match that to anything in this store. I can help with: {listing}. "
                    "Tell me the category or a budget and I'll find a safe option."
                ),
                reasoning="No catalog category matched the request; no product proposal was made.",
                guardrail_status="not_applicable",
            )

        rejected: list[dict[str, str | float | int]] = []
        candidates: list[dict[str, Any]] = []
        for item in catalog:
            category = str(item.get("category", "")).lower()
            price = float(item.get("price", 0))
            if category not in wanted:
                reason = "wrong category"
            elif item.get("stock", 0) <= 0:
                reason = "out of stock"
            elif price > 8000:
                reason = "over the store per-order limit"
            elif budget is not None and price > budget:
                reason = f"over the ₹{budget:g} budget"
            else:
                candidates.append(item)
                continue
            rejected.append({
                "name": str(item.get("name", "Unknown product")),
                "category": category,
                "price": price,
                "reason": reason,
            })

        # Rank alternatives: same-category rejects (over budget / out of stock) are
        # more relevant than wrong-category fillers when explaining the decision.
        rejected.sort(key=lambda r: 0 if r["category"] in wanted else 1)

        if not candidates:
            in_stock = [
                item for item in catalog
                if str(item.get("category", "")).lower() in wanted and item.get("stock", 0) > 0
            ]
            if budget is not None and in_stock:
                cheapest = min(in_stock, key=lambda item: float(item["price"]))
                message = (
                    f"Nothing in {self._pretty_categories(wanted)} is under ₹{budget:g} right now — "
                    f"the closest is {cheapest['name']} at ₹{float(cheapest['price']):g}. "
                    "Ask for it without the budget and I'll propose it."
                )
            elif in_stock:
                message = (
                    f"Everything in {self._pretty_categories(wanted)} exceeds the store's ₹8,000 "
                    "per-order limit, so I can't propose a safe checkout for it."
                )
            else:
                message = (
                    f"Everything in {self._pretty_categories(wanted)} is out of stock right now. "
                    "Please check back soon or pick another category."
                )
            return AgentDecision(
                message=message,
                reasoning="No candidate satisfied the request filters; no product proposal was made.",
                guardrail_status="not_applicable",
                candidates_considered=rejected[:3],
            )

        best_match = min(candidates, key=lambda item: float(item["price"]))

        candidate_budget = float(best_match["price"])
        # Explainability: alternatives that passed every filter but cost more come
        # first; filter-rejected items fill the remaining slots.
        pricier = [
            {
                "name": str(item.get("name", "Unknown product")),
                "category": str(item.get("category", "unknown")),
                "price": float(item.get("price", 0)),
                "reason": "in stock but more expensive than the selected match",
            }
            for item in candidates
            if item.get("id") != best_match.get("id")
        ]
        considered = (pricier + rejected)[:3]

        budget_note = f", fits the ₹{budget:g} budget" if budget is not None else ""
        return AgentDecision(
            message=(
                f"I found {best_match['name']} for ₹{candidate_budget:g}. I recommend buying it because it "
                f"matches your request{budget_note} and stays within the allow-listed category."
            ),
            reasoning=(
                f"selected {best_match['name']} because price ₹{candidate_budget:g} matches the request "
                f"and category '{best_match['category']}' is approved for purchase."
            ),
            product_id=best_match["id"],
            amount=candidate_budget,
            guardrail_status="passed",
            candidates_considered=considered[:3],
            upsell_product=self._find_upsell(best_match, catalog),
            cross_sell_products=self._find_cross_sells(best_match, catalog),
        )

    def _match_categories(self, text: str) -> set[str]:
        """Detect which catalog categories the message asks about."""
        wanted: set[str] = set()
        for tier in (TIER1_CATEGORY_KEYWORDS, TIER2_CATEGORY_KEYWORDS):
            if wanted:
                break
            for category, keywords in tier.items():
                if any(re.search(rf"\b{re.escape(keyword)}\b", text) for keyword in keywords):
                    wanted.add(category)
        return wanted

    def _extract_budget(self, text: str) -> Optional[float]:
        """Parse an explicit budget such as 'under ₹900' or 'below 2000'."""
        match = BUDGET_PATTERN.search(text)
        if not match:
            return None
        value = float(match.group(1))
        return value if value > 0 else None

    def _is_conversational(self, text: str, wanted: set[str]) -> bool:
        """Greetings, small talk, and acknowledgements should never return products."""
        if wanted:
            return False
        if not text:
            return True
        words = re.findall(r"[a-z']+", text)
        if words and len(words) <= 4 and all(word in GREETING_WORDS for word in words):
            return True
        if words and words[0] in GREETING_WORDS and len(words) <= 5:
            return True
        return any(phrase in text for phrase in CONVERSATIONAL_PHRASES)

    def _pretty_categories(self, categories: set[str]) -> str:
        names = sorted(categories)
        if not names:
            return "this category"
        if len(names) == 1:
            return names[0]
        return ", ".join(names[:-1]) + " or " + names[-1]

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
