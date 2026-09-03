<p align="center">
   <img src="assets/logo.jpg" alt="AuditPay logo" width="180" style="border-radius: 20px>
</p>
<h1 align="center">AuditPay</h1>

<p align="center">
   A safe, explainable AI shopping agent with deterministic guardrails and a complete audit trail.
</p>

<p align="center">
   <a href="#quick-start-docker">Quick start</a> ·
   <a href="#what-youll-see-when-you-open-it">Features</a> ·
   <a href="#architecture-overview">Architecture</a> ·
   <a href="#manual-non-docker-setup">Development</a>
</p>

<br>

AuditPay is an AI shopping agent that completes purchases on a merchant's behalf — safely bounded by deterministic guardrails and fully auditable by a human after the fact.

## The problem

AI agents are increasingly expected to transact on a human's behalf, but there is no standard way for a merchant to trust that an autonomous agent will behave safely, stay within spend limits, or leave a trace a human can audit afterwards. This is the same trust problem emerging protocols like NPCI's UAP, ACP, AP2, and x402 are trying to standardize. AuditPay makes that problem concrete: it shows what "safe agent checkout" actually looks like when you enforce it in code rather than trusting the model.

## Quick start (Docker)

```bash
git clone <repo-url>
cd AUDIT_PAY
cp .env.example .env   # then fill in RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET
docker compose up --build
```

Once running, open:

- **Frontend:** http://localhost:5173
- **Backend API docs (Swagger):** http://localhost:8000/docs

The product catalog is seeded automatically on first boot. The compose file ships with Razorpay test-mode default keys, so if you skip the `.env` edit the backend runs in safe mock mode — checkout flows work end-to-end without touching real money.

## What you'll see when you open it

- **Storefront/catalog** — 8 seeded skincare products with prices, stock, and categories.
- **Agent chat** — type a request ("I need a moisturizer for dry skin"); the agent recommends a product, shows its reasoning, the candidates it considered and rejected, and optional upsell/cross-sell suggestions, then proposes a checkout.
- **Audit dashboard** — every agent action is logged with amount, reasoning, guardrail verdict, and outcome, plus a summary panel (session spend vs. the ₹9,000 cap, guardrail pass rate, failed payments).
- The dashboard starts empty and populates from real interactions — which is the point: the log records what actually happened, not a scripted demo. To see a guardrail rejection immediately, send a checkout through `/docs` with an amount above ₹8,000 (it's blocked and logged as `BOUNDS_REJECTED`), or use the simulate-failure toggle in the UI to see a logged `PAYMENT_DECLINED`. Approve a normal agent checkout and you'll have approved, blocked, and declined events in one view.

## Architecture overview

```
Browser (React storefront + agent chat)
      │
      ▼
FastAPI backend ──► Catalog API          (products, stock, categories)
      │
      ├──► Shopping agent               (recommends product + amount, explains reasoning)
      │         │
      │         ▼
      ├──► Guardrail layer  ──► REJECT ─► logged as audit event, nothing moves
      │    (deterministic, non-LLM)
      │         │ pass
      │         ▼
      └──► Razorpay test-mode API       (order created only if all guardrails clear)
                │
                ▼
           Audit log (every decision, pass or fail)
```

Every checkout request — whether triggered by a human clicking buy or by the agent proposing a purchase — flows through the guardrail layer before Razorpay is ever called. Rejected requests never reach the payment provider; they're recorded as audit events instead.

## Design decision: where the trust boundary lives

The recommendation logic in this project is intentionally simple: it does not try to be a deep constrained optimizer, and it is not a dedicated defense against prompt injection at the model layer. That is a deliberate design choice. The trusted boundary is the deterministic guardrail layer in `backend/core/guardrails.py`, which gates every financial action before a payment is attempted. The LLM is allowed to propose a product or amount, but it is never given authority to move money on its own; approval is enforced by a separate, non-LLM policy check that sits outside the model's judgment.

## Relationship to emerging agentic commerce protocols

This project is a small, concrete illustration of the trust problem that protocols such as NPCI's UAP, ACP, AP2, and x402 are trying to standardize: an AI agent transacting on a merchant's behalf must be able to discover a machine-readable catalog, make a bounded recommendation, and complete a checkout only when the transaction is safe, auditable, and within explicit guardrails. In other words, the catalog endpoint and the gated checkout flow model the same core need behind these emerging standards: trusted agent-to-merchant interaction with policy enforcement and a verifiable trail.

This project does not implement any of those protocols directly. It is intentionally a lightweight demo that makes the underlying trust, safety, and audit pattern visible without claiming to be a production-ready protocol stack.

## What's actually enforced

All guardrails live in `backend/core/guardrails.py` and run server-side before any payment call. Current configured values:

| Guardrail | Value |
|---|---|
| Max order value per transaction | ₹8,000 (`MAX_ORDER_VALUE`) |
| Max orders per session | 3 (`MAX_ORDERS_PER_SESSION`) |
| Max total spend per session (aggregate) | ₹9,000 (`MAX_SESSION_TOTAL_VALUE`) |
| Category allow-list | moisturizer, sunscreen, serum, cleanser, face oil, sets, makeup, skincare, wellness |

Additionally enforced on the checkout path: amounts must be positive numbers, the session order-limit check runs together with the aggregate spend cap, and a risk scorer can block a transaction before Razorpay is contacted. Every enforcement decision (pass or fail) is written to the audit log with its reasoning.

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy, SQLite |
| Frontend | React, Vite |
| Payments | Razorpay Python SDK (test mode) |
| Deployment | Docker Compose |

## Manual (non-Docker) setup

If you'd rather run the backend and frontend separately:

1. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Copy environment variables:
   ```bash
   cp .env.example .env
   ```
4. Start the API (port 8000):
   ```bash
   python -m backend.main
   ```
5. In another terminal, start the frontend (port 5173):
   ```bash
   cd frontend && npm install && npm run dev -- --host 0.0.0.0 --port 5173
   ```
6. Open the app at http://localhost:5173

## Testing

The project can be tested at the unit, database, frontend build, and Docker levels.

- **Run all backend tests:**
   ```bash
   python3 -m pytest backend/tests -q
   ```
- **Test guardrails:** `backend/tests/test_guardrails.py` covers transaction amount limits, category rejection, session order limits, and aggregate spend caps.
- **Test database schema:** `backend/tests/test_schema_verification.py` verifies that the required tables, including `saved_products`, are available.
- **Verify saved-product persistence:** save a product from the agent flow, refresh the browser, and confirm it remains in the Saved view. Remove it and refresh again to confirm it is deleted.
- **Check the API directly:** open `http://localhost:8000/docs` and test `/api/catalog`, `/api/saved`, `/api/agent`, and `/api/checkout`.
- **Build the frontend:**
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```
- **Validate Docker startup:**
   ```bash
   docker compose up --build
   ```
   Then open `http://localhost:5173` and `http://localhost:8000/health`.
- **Check formatting changes:**
   ```bash
   git diff --check
   ```

For a quick backend-only run:

```bash
python3 -m pytest backend/tests -q
```

## Project structure

```text
AUDIT_PAY/
├── backend/
│   ├── main.py                    # FastAPI application and startup lifecycle
│   ├── requirements.txt           # Python dependencies
│   ├── Dockerfile                 # Backend container image
│   ├── core/
│   │   ├── agent_llm.py           # Agent recommendation logic
│   │   ├── agent_tools.py         # Catalog search tools
│   │   ├── audit_trail.py         # Audit event recording
│   │   ├── campaigns.py           # Campaign and bundle logic
│   │   ├── guardrails.py          # Server-side trust boundary
│   │   ├── idempotency.py         # Duplicate payment protection
│   │   ├── immutable_audit.py     # Hash-linked audit entries
│   │   ├── payment_analytics.py   # Payment metrics
│   │   ├── razorpay_client.py     # Razorpay test-mode client
│   │   ├── risk_scorer.py         # Transaction risk checks
│   │   └── webhook_security.py    # Webhook verification
│   ├── db/
│   │   ├── models.py              # Product, SavedProduct, Order, and audit models
│   │   ├── schema.py              # Schema creation and verification
│   │   ├── seed.py                # Initial catalog data
│   │   └── session.py             # SQLAlchemy engine and sessions
│   ├── routes/
│   │   ├── agent.py               # Agent recommendations
│   │   ├── analytics.py           # Payment analytics
│   │   ├── audit.py               # Audit dashboard data
│   │   ├── audit_trail.py         # Detailed audit entries
│   │   ├── campaigns.py           # Campaign endpoints
│   │   ├── catalog.py             # Product catalog
│   │   ├── checkout.py             # Guarded checkout
│   │   ├── saved.py               # Saved-product persistence
│   │   └── webhooks.py            # Razorpay webhooks
│   └── tests/
│       ├── test_guardrails.py     # Guardrail regression tests
│       └── test_schema_verification.py # Database schema tests
├── frontend/
│   ├── Dockerfile                 # Frontend container image
│   ├── package.json               # Frontend dependencies and scripts
│   └── src/
│       ├── App.tsx                # Storefront, agent, saved items, and audit UI
│       ├── index.css              # Global styles
│       └── main.tsx               # React entry point
├── lib/
│   ├── api-client-react/          # Generated React API client
│   ├── api-spec/                  # OpenAPI contract and code generation
│   ├── api-zod/                   # Generated Zod API schemas
│   └── db/                        # Drizzle workspace database package
├── artifacts/                     # Additional prototype/workspace applications
├── scripts/                       # Project utility scripts
├── docker-compose.yml             # Runs backend and frontend together
├── .env.example                   # Example local environment variables
├── package.json                   # Root workspace scripts
├── pnpm-workspace.yaml            # pnpm workspace configuration
├── tsconfig.json                  # Root TypeScript configuration
└── README.md
```

The local `auditpay.db` SQLite file is created at runtime and should remain uncommitted. Docker stores the database in the `auditpay_data` volume so saved products, orders, and audit records survive container restarts.
