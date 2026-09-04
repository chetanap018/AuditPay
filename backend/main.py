from __future__ import annotations

import os
import warnings
from contextlib import asynccontextmanager
from pathlib import Path

# Suppress urllib3 OpenSSL warning (system-level issue)
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+")

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.db.schema import ensure_schema
from backend.db.seed import seed_catalog
from backend.routes.agent import router as agent_router
from backend.routes.analytics import router as analytics_router
from backend.routes.audit import router as audit_router
from backend.routes.audit_trail import router as audit_trail_router
from backend.routes.campaigns import router as campaigns_router
from backend.routes.catalog import router as catalog_router
from backend.routes.checkout import router as checkout_router
from backend.routes.saved import router as saved_router

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    ensure_schema()
    seed_catalog()
    yield
    # Shutdown (cleanup can go here)


app = FastAPI(
    title="AuditPay",
    description="AI shopping agent demo with explainable guardrails and audit trail.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog_router, prefix="/api")
app.include_router(agent_router, prefix="/api")
app.include_router(campaigns_router, prefix="/api")
app.include_router(checkout_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(saved_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(audit_trail_router, prefix="/api")


@app.get("/health")
def health() -> dict:
    schema_status = ensure_schema()
    return {"status": "ok", "service": "auditpay", "schema": schema_status}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)
