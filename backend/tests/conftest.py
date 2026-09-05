"""Test-session bootstrap.

On a fresh checkout no ``auditpay.db`` file exists yet, so schema-level tests
would fail. This session-scoped, autouse fixture creates the schema once before
the suite runs, making the tests self-contained.
"""

import pytest

from backend.db.schema import ensure_schema


@pytest.fixture(scope="session", autouse=True)
def prepare_database() -> None:
    """Create all required tables so schema tests pass on a clean clone."""
    ensure_schema()