# HCL DevOps Test Hub — API Test DSL Guide

Task-focused reference for writing **API (REST/JSON over HTTP) tests** for DevOps Test Hub as
hand-authored YAML. Read `dsl-guide.md` first for file types, variables, modules and suites — all of
that applies unchanged. This guide covers only what is specific to the `send` step.

Why hand-authored: in the Test Hub 12.0 tech preview the only built-in way to create an API test is
**recording** (browser ↔ backend traffic matched against an imported schema); there is no palette to
build one visually. YAML committed to the test repository opens fine and renders in the visual view as
`Send <url>` → `Send Request` / `Receive Response` → one node per check **[project run: Health Check,
passing and rendering]**. So generating YAML is currently the way to create API tests by hand.

Evidence tags (same idea as the browser guide): **[project run]** passed in Test Hub,
**[live API]** the behaviour was exercised against the real service by an independent client,
**[sample: path]** present in the vendor corpus (`onetest-ideas-dsl`, an HCL-internal repo — cite paths,
don't copy files into public repos), **[schema]** valid per `schemas/script.json`,
**[authored]** written and schema-valid but not yet confirmed in a Test Hub run. Prefer a construct with
a sample or a passing run behind it, and say which tag you are relying on.

## What the DSL gives you

| Need | Construct |
|---|---|
| Call an endpoint | `send:` with `url` (plain) or `schema: <openapi file>#<operationId>` |
| Set method, headers, body, auth | `request.fields` — `method`, `headers/<name>`, `content`, `auth/bearer/token`, `url/path/<param>`, `query/<name>` |
| Assert status / headers / JSON fields | `response.fields` — `status-code`, `headers/<name>`, `content/<json/path>` |
| Capture a value for later | `- var: NAME` as the value of a response field |
| Arithmetic / cross-call checks | `verify: [js expressions]` over captured vars |
| Reuse a flow (login, setup) | a module `.dtx.yaml` invoked with `run:` and `out:` vars |
| Reuse request/response shapes | `.dtm.yaml` messages via `includes:` **[sample: public/messages.dtx.yaml]** |
| Auth refresh on every request | `.dtt.yaml` transport with `hooks.request` **[sample: scripts/hooks/token-transport.dtt.yaml]** |

Everything else in `script.json` (`if`, `iterate`, `while`, datasets, `type: column`, `run:`) works
around `send` exactly as in browser tests.

## The `send` step

```yaml
- send:
    note: GET /health
    url: ${BASE_URL}/health            # [project run]
    request:
      fields:
        - method:
            - val: GET
        - headers/accept:
            - val: application/json
    response:
      fields:
        - status-code:
            - val: '200'
        - content/status:
            - val: ok
        - content/database:
            - var: DATABASE            # capture, usable as ${DATABASE} / in verify
```

The exact shape above (item-list values, `status-code`, `content/<field>`) is the one **confirmed passing
in Test Hub**. Keep to it unless you have a reason and a tag.

### Request fields

| Field path | Meaning | Evidence |
|---|---|---|
| `method` | `GET` (default), `POST`, `PUT`, `DELETE` | [project run] GET; [sample] POST |
| `headers/<name>` | any request header, e.g. `headers/content-type` | [project run] accept; [sample] content-type |
| `content` | raw body string. For JSON write the JSON as a single-quoted YAML string: `- val: '{"email":"${EMAIL}"}'` | [sample: messages.dtx.yaml] |
| `auth/bearer/token` | `Authorization: Bearer <token>` | [sample: scripts/auth/non-oauth2.dtx.yaml]; [authored] in the item-list form |
| `headers/authorization` | alternative: `val: 'Bearer ${TOKEN}'` | [sample: scripts/hooks/token-transport.dtt.yaml] |
| `url/path/<param>` | fill a `{param}` in a schema-driven send | [sample: scripts/openapi/openapi.dtx.yaml] |
| `query/<name>` | query-string parameter | [sample: api-record/basic-get/result/gen.dtx.yaml] |

Interpolation `${VAR}` / `${js}` works inside `url` and inside `val` strings. A JSON body can contain
`${...}`; plain `{`/`"` characters are fine.

### Response fields — checks and captures

- `status-code`: always assert it, including for expected errors: `- val: '404'`. Non-2xx statuses are
  declared like any other **[schema; sample: `'201'` in scripts/openapi/openapi.dtx.yaml, `'401'` in a response
  hook in scripts/hooks/token-transport.dtt.yaml; a 4xx expectation on a plain `send` is [authored]]**.
- `content/<path>`: JSON path with `/` separators, e.g. `content/user/email`. `- val: x` asserts equality
  (numbers compare as their string form: `content/id` with `val: '1'` matches `1`
  **[sample: scripts/openapi/openapi.dtx.yaml `content/id: '2'`]**).
- `- var: NAME` captures instead of asserting. JSON numbers stay numbers (`verify: RESULT === 15`
  **[sample: public/messages.dtx.yaml]**); still wrap in `Number(...)` before arithmetic — it costs nothing.
- Other value kinds in a field list: `regex`, `starts`, `ends`, `includes`, `js`, `optional`, `src`
  (file) **[schema: FieldItem]**; `regex` on `status-code` **[sample: scripts/openapi/validate-test.dtx.yaml]**.
- **Whole body**: `- content:` then `- var: BODY` captures the entire response **[sample: internal/example-com.dtx.yaml
  logs it]**. Whether the captured value is a string or an already-parsed object is not documented — parse
  defensively (see helper below). **[authored]**
- **Arrays of objects under a key**: `content/items/*` with `- repeat: {}` then `- fields:` capturing per-element
  values; each captured var becomes an array **[sample: internal/openapi/phonebook.dtx.yaml
  `content/entries/*`, then `IDS.length`, `IDS[0]`]**. A root-level JSON array has no sample — use whole-body
  capture for those instead.

### Schema-driven sends

```yaml
- send:
    schema: schemas/service-openapi.yaml#getHealth     # operationId after '#'
    response:
      fields:
        - status-code:
            - val: '200'
```

**[sample: scripts/openapi/*, api-record/basic-get/result/gen.dtx.yaml]**. The step takes the method, path
and server from the OpenAPI operation. Requirements: every operation needs a unique `operationId`;
path parameters are filled with `request: url/path/<param>`; the recorder's own output also pins
`url: fields: scheme/host` explicitly. How `servers` (with a base path like `/api`) is resolved is **not
confirmed** — if a schema-driven send hits the wrong URL, add a step-level `url:` (both `schema` and `url`
are allowed on a step) and record what worked.

## Capturing, comparing, helper functions

```yaml
configuration:
  vars:
    BASE_URL: http://localhost:5000/api
    PARSE:                                     # function as a variable [sample: modules-vars/functions.dtx.yaml]
      expr: 'b => typeof b === "string" ? JSON.parse(b) : b'
      type: js
steps:
  - send: { ... response: { fields: [ { content: [ { var: LIST } ] } ] } }
  - verify:
      - 'PARSE(LIST).length >= 1'
      - 'PARSE(LIST).every(p => Number(p.price) > 0)'
```

- `verify` takes a **list** of JS expressions, all must hold **[schema; works on both server schema versions]**.
- Money: compare with a tolerance — `Math.abs(Number(TOTAL) - 2 * Number(PRICE)) < 0.005`.
- Repeat-captured vars: normalise with `[].concat(X)` so one element and many elements behave the same.
- Unique test data: `assign` once, never rely on a var default being re-evaluated:
  `assign: vars: { EMAIL: '${"apitest+" + Date.now() + "-" + Math.floor(Math.random()*100000) + "@example.com"}' }`.
- Every `${VAR}` must be declared in the script's `configuration.vars` or arrive via `run: in:` — except
  captured/assigned vars, which the samples use undeclared. Declaring caller-side targets of `run: out:`
  with a literal `''` default is harmless and removes doubt.

## Modules, auth and chaining

A login module that returns a token — the backbone of workflow tests **[authored]**:

```yaml
configuration:
  vars:
    BASE_URL: http://localhost:5000/api
    EMAIL:    { expr: unset, modifier: out }
    PASSWORD: { expr: unset, modifier: out }
    TOKEN:    { expr: unset, modifier: out }
    USER_ID:  { expr: unset, modifier: out }
steps:
  - assign: { vars: { EMAIL: '...generated...', PASSWORD: '...generated...' } }
  - send: { ...register... }
  - send: { ...login..., response: { fields: [ ..., { content/token: [ { var: TOKEN } ] }, { content/user/id: [ { var: USER_ID } ] } ] } }
```

Caller: `run: { url: ../modules/Register And Login.dtx.yaml, out: { TOKEN: {}, USER_ID: {}, EMAIL: {}, PASSWORD: {} } }`.
Rename an output to run the module twice (two users): `out: { TOKEN: [TOKEN_B], USER_ID: [USER_B] }`
**[schema; rule from the browser guide: `out: {X: {}}` or `out: {X: [Y]}` work on both schema versions]**.

Then `request` of the next call uses `auth/bearer/token: [ { val: '${TOKEN}' } ]`. A failing step aborts the
whole test; in a suite the next test still runs.

## Designing a useful API suite

Build four tiers; keep each test independently runnable:

1. **Atomic** — one call, one idea: `GET Health`, `GET Product By Id`, `GET Product Not Found` (404 + error
   body), `GET Profile No Token` (401). Read-only wherever possible. Assert status, error message text, and
   the shape/types of the fields that matter, not the whole body.
2. **Auth** — register, login valid/wrong/unknown/missing credentials, token present/invalid, access control
   (a normal user gets 403 on an admin route; no token gets 401). Use generated throwaway users.
3. **Workflows** — chain calls and assert *relationships*: price in the order equals the catalog price;
   `total = Σ quantity × price`; stock falls by the quantity ordered; list view matches detail view; user B
   cannot see user A's order. This tier finds the real bugs.
4. **Known Issues** — a test that asserts the *correct* behaviour of a defect you have confirmed live, in its own
   folder and suite, excluded from the "all" suite. It fails until fixed, then guards the fix. State the
   defect and the current (wrong) response in the test `note`.

Naming: `GET Health`, `POST Login Wrong Password`, `Order Quantity 2 Totals And Stock` — verb + resource for
atomic/auth, an outcome sentence for workflows. One suite per tier plus an "All" suite that nests them.
Suites: `note` + `tests` only until suite `configuration` is confirmed on the target server.

## Grounding procedure (API equivalent of live-DOM discovery)

1. **Contract.** Use the OpenAPI/Swagger doc if one exists (`/api-docs`, `/swagger.json`, a file in the repo — check
   `swagger.js`-style generators too). If none, derive operations from router source and docs; if neither is
   available, ask. Record auth scheme, base URL and proxy/base path.
2. **Identify the service you are really talking to** before trusting it: `curl.exe -i <url>` and read `Server`,
   `X-Powered-By` and unusual headers. (A host's port 5000 turned out to be a Docker registry —
   `Docker-Distribution-Api-Version` — and the real API sat behind an nginx on :3000 that proxied only `/api`.)
3. **Probe read-only operations first**, then writes. Capture the *exact* status code, error string and field
   names; never assert text you have not seen. Note which operations change state.
4. **Probe error paths** that the contract implies (missing field, bad id, no/invalid token, wrong role).
5. **Replicate every planned assertion with an independent client** (a short Python/PowerShell script) before
   publishing. It catches wrong expectations cheaply and finds defects (which then go to Known Issues).
6. **Do not** forge tokens, guess admin credentials or password-spray to reach admin operations; ask the user
   for an admin token via an environment secret, or leave admin writes as documented-but-untested. **Do not**
   send inputs the source shows are unvalidated and could corrupt data (negative or zero quantities, huge
   payloads) to a shared host. Point deletes/updates at ids that cannot exist when probing protection.
7. Generate, validate, then ask the user to run `Atomic` first, `Auth` second, `Workflow` last, and bring back the
   failing step and message. Diagnose from the real failure; change one thing at a time.

Shell pitfalls on Windows: PowerShell 5.1's `curl` is an alias for `Invoke-WebRequest` (it prompts `Uri:` when
given `-i`) — use **`curl.exe`**, and escape inner quotes in `-d '{\"a\":1}'`. Bash blocks with `\` continuations
and `TOKEN=...` don't run in PowerShell. `Invoke-WebRequest` loses the response body on 4xx/5xx unless you read
`$_.Exception.Response.GetResponseStream()` in the catch block.

## Writing an OpenAPI file when none exists

Derive it from the router/handlers and **verify against the live service**. Give every operation a unique
`operationId` (schema-driven sends need it; the recorder most likely matches on it). Put the base path either in
`servers` or in every path, consistently, and note which. Mark per operation how it was established (a custom
`x-verified: live | live-failing | source` is handy) and list confirmed defects under a top-level
`x-known-issues`. Validate it parses and every `$ref` resolves. See
`../examples/SendItCycles-API/schemas/senditcycles-openapi.yaml`.

## Recording ("no interactions matched")

When a Test Hub API recording finds nothing, check before concluding the UI uses different APIs: the browser
usually calls the same `/api/...` the spec describes. Candidate causes, **unconfirmed**: the spec's `servers`
host/port differs from the traffic's (proxy on :3000 vs backend on :5000); the base path is split between `servers`
and `paths` so full request paths don't match any path template; operations lack `operationId`s. Test one
change at a time.

## Server schema versions

Same rules as the browser guide's "Server schema versions" section. For `send`: write field values as item lists
(`key: [{val: ...}]`), `verify` as a list, `out:` targets as `{X: {}}` / `{X: [Y]}`. The scalar shorthand
(`status-code: '200'`) is only valid on the newer schema.

## Construct status — update this table from Test Hub results

| Construct | Status |
|---|---|
| Plain-URL `send`, `method`, `headers/accept`, `status-code`, `content/<field>` equality | **[project run] passing** |
| `content/<field>` with `- var:` capture, `${VAR}` in url, `verify: [...]` | [authored] — Test Hub result not yet recorded |
| `request` body via `content` + `headers/content-type`, `POST` | [authored] |
| `auth/bearer/token` in item-list form | [authored] |
| Whole-body capture + `PARSE` helper (JSON.parse in a function var) | [authored], highest risk |
| `content/items/*` + `repeat` array capture | [authored] (sample uses object-keyed arrays) |
| Module `out:` incl. renamed outputs (`TOKEN: [TOKEN_B]`) | [authored] |
| Schema-driven `schema: file#operationId` and `servers` resolution | [authored] |

After a run, move each row to `[project run] passing` or note the exact failure and the fix.
See the worked example and its `LIVE-NOTES.md` in `../examples/SendItCycles-API/`.
