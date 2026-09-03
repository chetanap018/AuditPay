from __future__ import annotations

from typing import Any

from sqlalchemy import inspect, text  # type: ignore[reportMissingImports]

from backend.db.models import Base
from backend.db.session import SessionLocal, engine

REQUIRED_TABLES = [
    "products",
    "saved_products",
    "orders",
    "agent_actions",
    "idempotency_keys",
    "audit_log",
]

# Lightweight auto-migrations: columns added after a table was first created.
# SQLite ALTER TABLE only supports ADD COLUMN, which is all we need here.
AUTO_MIGRATIONS: dict[str, dict[str, str]] = {
    "agent_actions": {
        "candidates_considered": "TEXT",
        "risk_score": "FLOAT",
        "risk_factors": "TEXT",
    },
    "orders": {
        "total": "FLOAT DEFAULT 0",
        "razorpay_order_id": "VARCHAR(255)",
        "razorpay_payment_id": "VARCHAR(255)",
        "idempotency_key": "VARCHAR(128)",
        "risk_score": "FLOAT",
        "risk_factors": "TEXT",
    },
    "audit_log": {
        "entry_hash": "VARCHAR(64)",
        "previous_hash": "VARCHAR(64)",
    },
}


def ensure_schema() -> dict[str, Any]:
    """Create database tables if missing, apply column migrations, verify."""
    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        inspector = inspect(conn)
        for table, columns in AUTO_MIGRATIONS.items():
            existing = {col["name"] for col in inspector.get_columns(table)}
            for column, column_type in columns.items():
                if column not in existing:
                    conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
                    )

    return verify_schema()


def verify_schema() -> dict[str, Any]:
    """Check whether the required application tables exist in the database."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    missing = [table for table in REQUIRED_TABLES if table not in tables]

    return {
        "status": "ok" if not missing else "missing_tables",
        "tables": sorted(tables),
        "missing": missing,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(ensure_schema(), indent=2))
