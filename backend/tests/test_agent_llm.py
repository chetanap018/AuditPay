from backend.core.agent_llm import AgentLLM


def build_catalog():
    return [
        {"id": 1, "name": "Cloudmilk Barrier Cream", "description": "soothing moisturizer", "price": 649, "stock": 18, "category": "moisturizer"},
        {"id": 2, "name": "Dewdrop Daily Sun Shield", "description": "lightweight sunscreen", "price": 799, "stock": 21, "category": "sunscreen"},
        {"id": 3, "name": "Glowcore Vitamin C Serum", "description": "brightening serum", "price": 899, "stock": 15, "category": "serum"},
        {"id": 4, "name": "Petal Reset Cleanser", "description": "low-foam gel cleanser", "price": 549, "stock": 32, "category": "cleanser"},
        {"id": 6, "name": "Hydra Duo Starter Set", "description": "cleanser, serum, and moisturizer routine", "price": 1499, "stock": 7, "category": "sets"},
    ]


def test_greeting_does_not_recommend():
    decision = AgentLLM().decide("hi", build_catalog())
    assert decision.product_id is None
    assert decision.amount is None
    assert decision.guardrail_status == "not_applicable"


def test_short_smalltalk_is_conversational():
    for message in ("hello", "hey there", "thanks", "ok", "namaste", "how are you"):
        decision = AgentLLM().decide(message, build_catalog())
        assert decision.product_id is None, f"'{message}' should not return a product"


def test_out_of_domain_request_clarifies():
    decision = AgentLLM().decide("I want to buy a laptop", build_catalog())
    assert decision.product_id is None
    assert "couldn't match" in decision.message.lower()


def test_moisturizer_request_recommends_matching_category():
    decision = AgentLLM().decide("I need a gentle moisturizer", build_catalog())
    assert decision.product_id == 1
    assert decision.guardrail_status == "passed"
    assert decision.amount == 649


def test_sunscreen_budget_is_respected():
    decision = AgentLLM().decide("Best sunscreen under ₹900", build_catalog())
    assert decision.product_id == 2
    assert decision.amount == 799


def test_budget_with_no_match_clarifies_instead_of_overspending():
    decision = AgentLLM().decide("a sunscreen under ₹100", build_catalog())
    assert decision.product_id is None
    assert "under" in decision.message.lower()


def test_serum_request_stays_specific():
    decision = AgentLLM().decide("Hydrating serum for dry skin", build_catalog())
    assert decision.product_id == 3
    assert decision.amount == 899


def test_dry_skin_without_category_broadens_safely():
    decision = AgentLLM().decide("something for dry skin", build_catalog())
    assert decision.product_id in {1, 3}


def test_empty_message_is_conversational():
    decision = AgentLLM().decide("   ", build_catalog())
    assert decision.product_id is None