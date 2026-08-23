# Nila Agentic Commerce Demo

Nila is a pitch-ready AI shopping copilot that recommends products, explains every decision, and enforces spending guardrails before a Razorpay test checkout.

## Run & Operate

- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `pnpm --filter @workspace/agentic-commerce run dev` — run the frontend
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required env: `DATABASE_URL` — Postgres connection string

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)
- Frontend: React + Vite, Tailwind CSS, Wouter, TanStack Query

## Where things live

- `artifacts/agentic-commerce/src/App.tsx` — storefront, copilot, and audit routes
- `artifacts/agentic-commerce/src/index.css` — Nila visual language and motion
- `artifacts/api-server/src/core/guardrails.ts` — explicit order bounds and category allow-list
- `artifacts/api-server/src/data/store.ts` — demo catalog and explainable audit events
- `artifacts/api-server/src/routes/` — catalog, agent, checkout, and audit API handlers
- `lib/api-spec/openapi.yaml` — source of truth for generated API hooks and schemas

## Architecture decisions

- The frontend is resilient to an unavailable API so the product can still be demonstrated as a polished prototype.
- Guardrail decisions are enforced in server code before checkout and are also recorded as human-readable audit events.
- Payment decline is an intentional test-mode scenario with an explicit retry path rather than an unhandled error.

## Product

- Browse and search a small D2C catalog.
- Ask Nila for a natural-language recommendation with budget-aware matching.
- Confirm a bounded checkout, see a simulated payment decline, or follow the retry flow.
- Review action history, bounds checks, outcomes, and summary health metrics.

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

- Run API codegen after changing `lib/api-spec/openapi.yaml`.
- Artifact builds require `PORT` and `BASE_PATH` from the managed workflow; for an ad-hoc build set both explicitly.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
