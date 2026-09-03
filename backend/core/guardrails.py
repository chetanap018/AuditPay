from __future__ import annotations

from dataclasses import dataclass

MAX_ORDER_VALUE = 8000
MAX_ORDERS_PER_SESSION = 3
MAX_SESSION_TOTAL_VALUE = 9000
ALLOWED_CATEGORIES = {
    "moisturizer",
    "sunscreen",
    "serum",
    "cleanser",
    "face oil",
    "sets",
    "makeup",
    "skincare",
    "wellness",
}


@dataclass(frozen=True)
class GuardrailDecision:
    passed: bool
    reason: str


def check_order_bounds(amount: float, category: str) -> GuardrailDecision:
    """Validate amount and category before any payment call is made."""
    if not isinstance(amount, (int, float)) or amount <= 0:
        return GuardrailDecision(
            passed=False,
            reason="Order amount must be a positive number.",
        )

    if amount > MAX_ORDER_VALUE:
        return GuardrailDecision(
            passed=False,
            reason=(
                f"Order value ₹{amount} would exceed the configured maximum of "
                f"₹{MAX_ORDER_VALUE}; the chosen order exceeds the allowed per-order cap."
            ),
        )

    category_key = str(category).strip().lower()
    if category_key not in ALLOWED_CATEGORIES:
        return GuardrailDecision(
            passed=False,
            reason=(
                f'Category "{category}" is not on the approved purchase allow-list.'
            ),
        )

    return GuardrailDecision(
        passed=True,
        reason=(
            f"Amount ₹{amount} is within the ₹{MAX_ORDER_VALUE} limit and "
            f'category "{category}" is approved.'
        ),
    )


def check_session_total_spend(current_total: float, new_amount: float) -> GuardrailDecision:
    """Reject a new order when the running session total would exceed the cap."""
    if not isinstance(current_total, (int, float)) or current_total < 0:
        return GuardrailDecision(
            passed=False,
            reason="Session total spend must be a non-negative number.",
        )

    if not isinstance(new_amount, (int, float)) or new_amount <= 0:
        return GuardrailDecision(
            passed=False,
            reason="New order amount must be a positive number.",
        )

    next_total = float(current_total) + float(new_amount)
    if next_total > MAX_SESSION_TOTAL_VALUE:
        return GuardrailDecision(
            passed=False,
            reason=(
                f"Session total spend would rise from ₹{current_total} to ₹{next_total}, "
                f"exceeding the maximum session total of ₹{MAX_SESSION_TOTAL_VALUE}."
            ),
        )

    return GuardrailDecision(
        passed=True,
        reason=(
            f"Session total spend is ₹{next_total} of the ₹{MAX_SESSION_TOTAL_VALUE} total cap."
        ),
    )


def check_session_order_limit(
    order_count: int,
    current_total: float = 0.0,
    new_amount: float | None = None,
) -> GuardrailDecision:
    """Ensure the session has not exceeded the allowed number of bounded purchases or total value."""
    if not isinstance(order_count, int) or order_count < 0:
        return GuardrailDecision(
            passed=False,
            reason="Session order count must be a non-negative integer.",
        )

    if order_count >= MAX_ORDERS_PER_SESSION:
        return GuardrailDecision(
            passed=False,
            reason=(
                f"Session has reached the maximum of {MAX_ORDERS_PER_SESSION} "
                "orders."
            ),
        )

    if new_amount is not None:
        total_check = check_session_total_spend(current_total, new_amount)
        if not total_check.passed:
            return total_check

    return GuardrailDecision(
        passed=True,
        reason=(
            f"Session has {MAX_ORDERS_PER_SESSION - order_count} bounded order "
            "slot(s) remaining and stays within the session total cap."
        ),
    )
