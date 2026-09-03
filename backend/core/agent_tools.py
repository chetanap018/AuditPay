from __future__ import annotations

from typing import Any


def search_catalog(catalog: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    q = (query or "").lower().strip()
    if not q:
        return catalog

    return [
        item
        for item in catalog
        if q in str(item.get("name", "")).lower()
        or q in str(item.get("description", "")).lower()
        or q in str(item.get("category", "")).lower()
    ]


def place_order(product: dict[str, Any], amount: float) -> dict[str, Any]:
    return {
        "product_id": product["id"],
        "product_name": product["name"],
        "amount": amount,
        "status": "ready_for_checkout",
    }
