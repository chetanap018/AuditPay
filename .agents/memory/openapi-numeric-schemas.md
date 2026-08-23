---
name: OpenAPI numeric schemas
description: Compatibility note for generated Zod schemas in this workspace.
---

Use `type: number` for numeric IDs, counts, and amounts in the OpenAPI contract unless the validation dependency is upgraded to a Zod runtime that supports generated integer helpers.

**Why:** The current code generator emitted `z.int()` for OpenAPI integer schemas, but the workspace's installed Zod runtime did not expose that helper, causing library typechecks to fail after otherwise successful codegen.

**How to apply:** After changing the schema, run API codegen and the library typecheck before wiring new generated types into routes or UI.