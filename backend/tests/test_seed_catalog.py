from backend.core.guardrails import ALLOWED_CATEGORIES
from backend.db.seed import build_seed_catalog


def _catalog():
    return build_seed_catalog()


def test_every_allow_listed_category_is_seeded():
    seeded = {item["category"] for item in _catalog()}
    assert ALLOWED_CATEGORIES == seeded


def test_each_category_has_at_least_two_products():
    counts: dict[str, int] = {}
    for item in _catalog():
        counts[item["category"]] = counts.get(item["category"], 0) + 1
    for category in ALLOWED_CATEGORIES:
        assert counts[category] >= 2, f"category '{category}' has only {counts[category]} product(s)"


def test_each_category_spans_different_price_ranges():
    prices: dict[str, list[float]] = {}
    for item in _catalog():
        prices.setdefault(item["category"], []).append(float(item["price"]))
    for category, values in prices.items():
        distinct = sorted(set(values))
        assert len(distinct) >= 2, f"category '{category}' does not span different price ranges"


def test_all_seeded_categories_are_valid():
    for item in _catalog():
        assert item["category"] in ALLOWED_CATEGORIES


def test_all_seeded_products_are_within_per_order_limit_and_in_stock():
    from backend.core.guardrails import MAX_ORDER_VALUE

    for item in _catalog():
        assert 0 < item["price"] <= MAX_ORDER_VALUE, f"{item['name']} price out of bounds"
        assert item["stock"] > 0, f"{item['name']} is out of stock on seed"
