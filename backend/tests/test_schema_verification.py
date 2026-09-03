from backend.db.schema import verify_schema


def test_verify_schema_reports_expected_tables():
    result = verify_schema()

    assert result["status"] == "ok"
    assert "products" in result["tables"]
    assert "saved_products" in result["tables"]
    assert "orders" in result["tables"]
    assert "agent_actions" in result["tables"]
    assert "audit_log" in result["tables"]
    assert result["missing"] == []
