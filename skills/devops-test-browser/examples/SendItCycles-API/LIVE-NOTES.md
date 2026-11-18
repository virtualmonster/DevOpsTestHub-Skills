# SendItCycles-API — live notes

Cache of facts confirmed by calling the real demo service (2026-11-18) and reading the repo
`virtualmonster/senditcycles` (`main`). Trust these for what they cover; re-verify after an app update or a data
reset. Tags: **[live]** called by an independent client, **[source]** from the repo, **[Test Hub]** from a run.

## Service and routing
- Express backend; `GET /api/health` → `{"status":"ok","timestamp":...,"database":"SQLite (Demo)"}` **[live]**. The demo
  runs SQLite although handlers use Postgres-style SQL and error codes — this explains several 500s below.
- docker-compose demo: frontend nginx on :3000 proxies the **`/api` prefix** to the backend on :5000 **[source]**. On the
  deployed host `/api-docs` (Swagger UI, served by the backend) fell through to the SPA, so it was **not reachable via
  the :3000 proxy** **[live]**; and port 5000 on that host was a Docker registry, not the API
  (`Docker-Distribution-Api-Version` header). Identify the service from its response headers before trusting a port.
- 25 operations are registered in `server/src/index.js` (no routers; `authMiddleware`, `adminMiddleware`) **[source]**.
- The repo's `swagger.js` defines only metadata and schemas; paths come from JSDoc in route files, so there is no
  complete served spec. `schemas/senditcycles-openapi.yaml` was written from source and verified live.
- Auth: JWT bearer token, default expiry 24h; the middleware splits on the first space and does not check the
  scheme word **[source]**. No token → 401 `No token provided`; bad token → 401 `Invalid token`; non-admin on an admin
  route → 403 `Admin access required` **[live]**.

## Response facts used by the tests [live]
- Register 201 → `{"message":"User registered successfully","user":{"id":N},"token":"..."}` (user has **only `id`**).
- Login 200 → `{"message":"Login successful","user":{id,email,first_name,last_name,role:"user"},"token":"..."}`.
- Profile 200 → `id,email,first_name,last_name,role,created_at`.
- Errors are `{"error":"<message>"}`: `Email and password required` (400), `Invalid credentials` (401, unknown email and
  wrong password alike), `Product not found` (404; also for non-numeric ids and 0), `Cart is empty` (400, empty or
  missing items), `Product 99999 not found` (404), `Insufficient stock for product 5` (400), `Order not found` (404, also
  for another user's order).
- Products: `id, category_id, name, description, price, stock_quantity, image_url, has_sizes, available_sizes, features,
  specs, geometry, created_at, updated_at, category_name`. `?limit=` is ignored (no pagination). 8 products, 5 categories.
- `POST /orders` → 201 order row **without items**; status `pending`; total computed server-side; stock decremented
  (verified: stock fell by the ordered quantity). `GET /orders/{id}` and `GET /orders` include `items`
  (`product_id, quantity, price, name`).
- Seed data: products 1–3 have thousands of units; product 5 has single-digit stock (used for the over-order test).

## Confirmed defects (the Known Issues tests) [live]
1. `GET /categories/{id}/products` → 500 `Database error` for every category (SQL uses alias `p` with no `FROM products p`).
2. Duplicate registration → 500 `Database error`, not 409 (handler maps only the Postgres `23505` code).
3. Malformed JSON body → 500 `Internal server error`, not 400.
Source-only, **not exercised**: `PUT /admin/*/bulk` is probably shadowed by `PUT /admin/*/:id`; order `quantity` is not validated
for sign/type (negative/zero not sent to a shared host); duplicate product ids in one order bypass the stock check.

## Test Hub results
- `GET Health` (plain `send`, item-list values, `status-code`, `content/status`) passes and renders as
  Send → Send Request / Receive Response → check nodes **[Test Hub]**.
- The other tests were authored and then replicated live (all assertions passed in an independent client). In Test Hub
  many pass and some do not; the failures are **not yet diagnosed** — record each here with the step, the message and
  the fix, and update the construct table in `reference/api-guide.md`.
- Test Hub 12.0 API **recording** against an imported schema reported "no interactions found" while browsing the app.
  The browser does call `/api/...`; suspected causes are unconfirmed (see `reference/api-guide.md`, "Recording").

## Side effects of running the suites
Auth and Workflow suites create throwaway users and orders; the order flows reduce stock of products 1, 2 and 3.
Stock-delta tests assume no concurrent orders of the same product.
