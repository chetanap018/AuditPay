from backend.core.guardrails import (
    check_order_bounds,
    check_session_order_limit,
)


def test_order_bounds_allow_valid_amount_and_category():
    result = check_order_bounds(650, "moisturizer")
    assert result.passed is True
    assert "approved" in result.reason.lower()


def test_order_bounds_reject_amount_above_limit():
    result = check_order_bounds(9000, "serum")
    assert result.passed is False
    assert "would exceed" in result.reason.lower()
    assert "₹9000" in result.reason
    assert "₹8000" in result.reason


def test_order_bounds_reject_disallowed_category():
    result = check_order_bounds(500, "home decor")
    assert result.passed is False
    assert "allow-list" in result.reason.lower()


def test_session_limit_rejects_when_does_not_have_room():
    result = check_session_order_limit(3)
    assert result.passed is False
    assert "maximum" in result.reason.lower()


def test_session_limit_allows_remaining_capacity():
    result = check_session_order_limit(1)
    assert result.passed is True
    assert "remaining" in result.reason.lower()


def test_session_total_spend_rejects_when_new_order_would_exceed_cap():
    result = check_session_order_limit(1, current_total=7000, new_amount=2500)
    assert result.passed is False
    assert "session total" in result.reason.lower()
    assert "maximum" in result.reason.lower()
