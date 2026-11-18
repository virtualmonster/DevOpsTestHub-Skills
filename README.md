# DevOps Test Hub skills

Claude Code skills for authoring and migrating HCL DevOps Test Hub tests: **browser/UI and API (REST/OpenAPI)**.

| Skill | Purpose |
|---|---|
| `skills/devops-test-browser` | Generate browser/UI **and API** test assets (`.dtx.yaml`, `.dts.yaml`, `.dtc.yaml`, data files) in the Test Hub DSL, grounded against the live application or service. Includes the DSL guide, an API (`send`) guide, JSON schemas (2026/07), 56 curated browser samples as precedent, and two worked components: `CycleStore` (browser) and `SendItCycles-API` (API). |
| `skills/maximo-testhub-migration` | Migrate IBM Maximo Test Automation Framework (MAS 9.1) browser tests into the Test Hub DSL, with live-confirmed MAS facts (deep-link app loading, iframe layout, consent banner behaviour, navigator pitfalls). |

The skill keeps its original name, `devops-test-browser`, so existing installs and the Maximo skill's references keep working; its scope is now both test kinds.

## API test generation (`devops-test-browser`)

In the Test Hub 12.0 tech preview the only built-in way to create an API test is recording browser traffic against an
imported schema; there is no palette for building one by hand. The skill fills that gap by writing the YAML directly (`send`
steps). Hand-authored files open in Test Hub and render as `Send <url>` → `Send Request` / `Receive Response` → one node per check.

**Ask for it in plain words**, for example:

- "Create a simple API test for the health endpoint."
- "Build atomic API tests for these endpoints from the OpenAPI file, then register/login flows."
- "Add workflow tests: get a product, order 2, and check the total and stock are correct."
- "Explain why this API test failed" (with a Test Hub result link or step output).

**What it does, in order**

1. **Inventory** the OpenAPI/Swagger doc or router source, base URL and auth scheme; reuse an existing component and its `LIVE-NOTES.md`.
2. **Ground live**: identify the real service from its response headers, probe reads then writes and the error paths, record the exact
   status codes, error strings and field names, and replicate every planned assertion with an independent client before publishing.
3. **Generate** four tiers, each independently runnable: *atomic* (one call, read-only where possible), *auth* (register, login, tokens,
   401/403), *workflows* (assert relationships: price × quantity = total, stock delta, list = detail, user isolation) and *known issues*
   (tests asserting the correct behaviour of confirmed defects, kept out of the "all" suite). One shared login module; one suite per tier.
4. **Validate** every file against the 2026/07 JSON Schemas, check `run:`/suite paths, and gate on API-specific rules (explicit status codes,
   item-list values, `run: out:` naming the caller variable, no literal secrets, no internal hosts in public repos).
5. **Publish** to the chosen branch, then ask for a Test Hub run (`Atomic` → `Auth` → `Workflow`) and diagnose from the real failure.

**Safety defaults**: throwaway data with per-run generated values and passwords; never forges tokens, guesses credentials or bypasses auth
(privileged calls need a token you supply through an environment secret); does not send inputs that could corrupt a shared host (negative or
zero quantities, oversized payloads); documents each suite's side effects.

**What is confirmed in Test Hub** (worked example `SendItCycles-API`, run 6217): all 26 tests in the Atomic, Auth and Workflow suites pass,
covering plain `send`, `${VAR}` URLs, captures, `verify` lists, POST bodies, expected 4xx with error text, whole-body capture with a JSON-parsing
helper, bearer auth, module `out:` mapping (including renamed outputs), array captures with `repeat`, and the stock/total/isolation
assertions. **Not yet run:** the Known Issues suite and schema-driven sends (`schema: file#operationId`).
The construct table in [`reference/api-guide.md`](skills/devops-test-browser/reference/api-guide.md) is the source of truth for what is confirmed
versus authored — update it from each Test Hub result.

**One gotcha worth knowing**: `run: out:` maps *module variable → caller variable* and the caller name must be spelled out
(`TOKEN: [TOKEN]`). An empty `TOKEN: {}` validates but maps nothing, so the caller gets an empty value.

**Not covered**: SQL, stubs (`.dtv`), gRPC and load profiles. Browser tests are unchanged.

## Install

Copy (or junction) each folder under `skills/` into `~/.claude/skills/` (Windows:
`%USERPROFILE%\.claude\skills\`). Claude Code picks them up on the next session.

## Layout

```
skills/<name>/SKILL.md            entry point read by Claude
skills/<name>/reference/          DSL guide, schemas, curated samples
skills/<name>/examples/           worked components (devops-test-browser only: CycleStore = browser, SendItCycles-API = API)
```

`skills/devops-test-browser/` in detail:

| Path | Contents |
|---|---|
| `SKILL.md` | Routing (browser vs API), operating model, permission policy, workflows for both test kinds, validation gates |
| `reference/dsl-guide.md` | File types, variables, step catalog, modules, suites, data-driven tests, schema versions |
| `reference/api-guide.md` | The `send` step, request/response fields, captures, schema-driven sends, auth and chaining, suite design, grounding procedure, confirmed-vs-authored table |
| `reference/schemas/` | Test Hub JSON Schemas (2026/07) |
| `reference/samples/` | Curated browser precedent (API patterns are described in `api-guide.md`, not copied) |
| `examples/CycleStore/` | Browser component example with `LIVE-NOTES.md` |
| `examples/SendItCycles-API/` | API component example: 30 tests, login module, 5 suites, OpenAPI 3 with `operationId`s, generator script, `LIVE-NOTES.md` (hosts sanitised to localhost) |
