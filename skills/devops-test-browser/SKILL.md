---
name: devops-test-browser
description: Generate browser/UI test artifacts (test scripts, modules, suites, components, data files) in HCL DevOps Test Hub's YAML/JSON DSL, ready to commit into a Test Hub git-backed test repository. Use when asked to create, generate, or extend browser or UI tests for DevOps Test Hub, or to explain/inspect its test DSL.
---

# DevOps Test Hub — Browser Test Generation

Generates test artifacts for **HCL DevOps Test Hub** in its native DSL, for **browser/UI
testing only** (API testing is a separate, not-yet-built extension to this skill — if asked for
API tests, say so rather than improvising against the `messages.json`/`transport.json` schemas).

## Operating model

Treat each request as a short evidence-to-result pipeline:

1. **Inventory** the project, branch, checkout, component, existing assets, smartshots, modules,
   and live notes.
2. **Decide once** what to generate, where it belongs, which evidence route to use, whether to
   compose modules, and where to push. Ask only for unresolved decisions in one batch.
3. **Ground** new selectors using the best available evidence: trusted live notes, usable
   smartshots, then targeted live-browser discovery for gaps or risk.
4. **Generate minimally**: prefer the smallest independent tests that cover the requested behavior,
   compose proven modules, and add a suite only when multiple tests need coordinated execution.
5. **Validate and publish**: check paths, schemas, references, diff, branch destination, and
   push only when requested or when the user's workflow clearly includes publishing.
6. **Verify in TestHub**: correlate results by project, branch, asset ID, and commit/version;
   diagnose real failures before editing, then make one evidence-based fix at a time.

Keep a compact session record of resolved choices (project, branch, component, generation route,
module policy, push destination). Reuse them for follow-up work in the same session unless the user
changes them. This prevents asking the same setup questions again while keeping branch and target
selection explicit.

## Permission and approval policy

Ask for approval once per session for the workflow defaults, then proceed without repeating the
same question. A single setup question can establish:

- the target project, branch, component, and application environment;
- smartshot, live-browser, or hybrid generation;
- module reuse versus self-contained tests;
- whether routine commits and pushes use the established temporary branch or `main`.

After those choices are established, continue automatically through routine discovery, browser
interaction on a confirmed test/staging URL, artifact generation, schema validation, local checks,
commit, and the established push destination. Do not ask again merely because another test uses the
same project, component, URL, module policy, or branch policy.

Pause and ask only when an action is materially different or consequential:

- the target looks like production or the environment/URL changes;
- the requested scope, component, branch, or destination is ambiguous;
- a destructive or externally visible application action is required and was not part of the
   established test workflow;
- credentials, offline tokens, or other secrets are needed;
- a generated change would overwrite unrelated user work or an existing asset;
- a TestHub failure presents multiple plausible fixes with different behavior.

When a pause is needed, batch all unresolved questions together and state the default you will use
if the user approves it. Treat a user instruction such as “go ahead,” “use the same settings,” or
“follow the previous pattern” as approval to reuse the established session defaults, not as a new
request for confirmation.

## Fast path for repeat work

When the same project/component has already been used in this session or has a current
`LIVE-NOTES.md`, use an incremental path:

1. Read the component definition and live notes first; do not rediscover documented routes,
   selectors, credentials policy, or module behavior.
2. Search only for assets relevant to the requested flow by name, route, feature, or module
   dependency. Do not enumerate every screenshot, DOM capture, or historical test unless the user
   asks for an inventory.
3. Compare the requested flow with existing tests and modules. Reuse a whole proven module or
   test asset rather than translating the same smartshots again.
4. Live-check only changed, high-risk, uncertain, or composition-boundary evidence. A stable
   confirmed fact does not need another browser session merely because a new test uses it.
5. Generate the smallest delta, validate only touched artifacts plus their direct `run:`/suite
   dependencies, and query only the resulting asset IDs after publishing.

Use a full discovery pass only when the component is new, the notes are absent/stale, the target
environment changed, or a TestHub failure contradicts the cached evidence. Treat `LIVE-NOTES.md`
as a cache with invalidation triggers, not as a permanent source of truth.

### Stop conditions

Stop discovery and move to generation when all of these are known:

- the exact project/team space, branch, repository checkout, and component;
- the target URL and requested scenario boundaries;
- the destination folder and test-versus-suite shape;
- the chosen evidence route and module policy;
- one grounded source for every new selector, with no unresolved high-risk seam.

Do not search unrelated components, enumerate all historical runs, or open every smartshot after
these conditions are met. Take one nearby read only when it can change a generation decision or
disambiguate a selector; otherwise proceed and let focused validation expose the next issue.

## Before generating anything

1. Read `reference/dsl-guide.md` — condensed guide to file types, step syntax, element
   locating, variables, data-driven testing, and the recommended generation workflow.
2. Look at `examples/CycleStore/` — **a bundled reference example only, for illustrating file
   layout and conventions; it is not tied to any real target application.** Real usage always
   targets whatever component/app the user names (see "Before writing anything" below) — never
   assume CycleStore/SendIt Cycles is the app under test. The example contains a full component
   (a fictional e-commerce site called "SendIt Cycles") with:
   - `.dtc.yaml` — the component definition
   - `LIVE-NOTES.md` — **check this before doing any live browser work against CycleStore.** It's
     a running cache of DOM facts already confirmed by actually driving the app in a past session
     (element mappings, quirks, which modules still match). Trust it for anything it covers;
     only live-verify what's genuinely new. Every component you work with accumulates one of
     these over time — check for it, and add to it when you confirm something new (see
     `reference/dsl-guide.md`).
   - `modules/` — reusable flows (Sign In, Sign Out, Add Product To Cart, Check Out, Checkout
     Product) invoked from tests via `run:`
   - Top-level tests (`Register User.dtx.yaml`, `Checkout Product.dtx.yaml`, `Admin Portal
     Login.dtx.yaml`) and a suite (`Deployment Verification UI Test Suite.dts.yaml`) that runs
     them together
   - `generated tests/` — an alternative style: one file per scenario plus its own suite,
     produced from a recorded session (note the richer `configuration.vars` shape with
     `expr`/`type`/`modifier`)
   - `RegisterUserData.ddf` plus `Card Details/`, `Currency/`, `Email/` — data-driven test data
     (generators and category markers)
3. When you need precedent for a construct — a step shape, a locator kind, frames, tabs,
   conditionals, environments, suite options — look in `reference/samples/` (see its README).
   These are the vendor's own runtime unit tests, curated; a construct present there is known to
   execute. Prefer a sample-backed construct over a schema-only one, and say which it is.
4. Only consult `reference/schemas/*.json` (the raw JSON Schemas) when the guide and samples
   leave a field's validity or shape unclear — `script.json` for tests/modules, `suite.json` for
   suites, `component.json` for components, `environment.json` for `.dte.yaml`. The other
   schemas (`messages`, `transport`, `stub`, `databasequery`, `loadprofile`) are the API/perf
   side; don't use them for browser test generation.
5. Quick check: is Test Hub's own MCP server (`testhub__*` tools) connected this session? If so,
   read `reference/testhub-mcp-tools.md` and use the discovery and result-review tools. Treat test
   execution as best-effort: the execution API may require a refresh token even when project and
   result tools work. Do not block generation or result review on `run_test` authentication.
   **Expect the server usually won't be connected** — in a managed/enterprise desktop app
   deployment this is commonly blocked by org policy (custom MCP connectors not allowed) and
   structurally awkward anyway (Test Hub is normally self-hosted per team/user, not one shared
   org-wide URL). Don't spend much effort chasing this if it isn't already set up.

## Inventory and decide once

When the user has not already named an exact project, branch, and component, resolve those before
writing test files. First gather available facts without asking: call `testhub__get_projects` once
when connected, inspect the current checkout and git remote, locate `.dtc.yaml`, `LIVE-NOTES.md`,
smartshots, modules, tests, suites, and relevant schema/examples. Then ask one batch containing
only decisions that remain ambiguous:

1. **Test Hub instance URL** — ask only when it is not available from the connected MCP server or
   an existing component/configuration. Do not request credentials in chat; authentication belongs
   in the user's MCP configuration.
2. **Repository URL** — when `testhub__get_projects` returns a repository/SCM URL for the selected
   project, use it to identify or obtain the git-backed test repository. If project metadata omits
   it, use the current checkout's remote URL; ask the user only when neither source is available.
3. **Project name or ID** — if MCP is connected, call `testhub__get_projects` and present the
   matching project names/IDs, including the team space when names are duplicated. Do not assume a
   project named `TestLoop` is unique.
4. **Branch/revision** — use the project's default/obvious branch when the user has clearly
   implied it; otherwise ask. Discovery and result review must use the same branch as the user's
   checkout and Test Hub integration.
5. **Component** — identify component folders from the checked-out Test Hub repository by finding
   `.dtc.yaml` files. Use the project's listed test assets as corroborating evidence when MCP is
   connected. There is no assumption that a Test Hub project name equals a component name.
6. **Test folder** — ask where generated tests belong if the component has multiple plausible
   folders; otherwise follow the component's existing layout. Never silently create a new parallel
   folder when a matching test folder already exists.
7. **Target application URL** — use the component's `.dtc.yaml` when present; ask if it is absent
   or multiple environments are plausible.
8. **Test organization** — ask whether to create individual tests or one suite only when the
   request describes multiple scenarios and the choice affects execution. A suite is useful for a
   coherent regression slice; separate tests are better when scenarios need independent reruns.
9. **Modules** — inspect existing modules before asking. If reusable candidates exist, ask whether
   to reuse them via `run:` or write fresh steps. If no candidates exist, ask whether the new flow
   should introduce reusable modules only when there is a genuine repeated sub-flow; keep a simple
   one-off test inline.

If the repository is not checked out or the component cannot be located, say exactly what is
missing and ask for the checkout/path before generating selectors. Do not invent component names
from the project list. The MCP project and test-list tools can discover project metadata and assets,
but cannot replace inspecting the repository's `.dtc.yaml`, module, and test files.

Use the following decision order to avoid redundant questions:

1. Project/team space and branch.
2. Repository checkout and component.
3. Target URL and requested scenarios.
4. Existing modules versus inline steps.
5. Smartshot, live-browser, or hybrid evidence route.
6. Test files versus suite organization.
7. Temporary branch versus `main` when publishing.

If the user asks for a broad goal such as “create smoke tests,” propose a small representative
set based on the application's existing flows and ask for confirmation only when scope materially
changes the files or risk. Do not turn every possible scenario into a regression suite by default.

## Choose the fastest grounded generation route

After locating the component and before starting an agent-driven browser session, search the
component/repository for smartshot artifacts. Do not assume a filename or schema: inspect the
actual files and recognize likely smartshots by their contents, metadata, or a `smartshots/`
folder. A smartshot is usable only when it provides enough trustworthy evidence for the requested
flow, such as the target URL/page, ordered user actions, and element identity or locator data.

If smartshots cover the requested flow, tell the user what was found and offer two choices:

- **Generate from smartshots** — translate the recorded evidence into Test Hub DSL, preserving the
   recorded order and using existing modules where appropriate. This is the fast path.
- **Use agent-driven browser discovery** — walk the live application to confirm or replace the
   recorded evidence. Choose this when the smartshot is stale, incomplete, ambiguous, or the user
   wants current DOM confirmation.

If the user has not expressed a preference, ask once when both choices are credible. If only part
of the flow is covered, propose a hybrid: use the smartshot for the covered portion and live-drive
only the missing or uncertain portion. If no usable smartshots are present, continue with the
browser-grounded workflow below without treating their absence as an error.

### Basic smartshot definition

For this skill, a **smartshot** is a repository-stored capture of browser interaction evidence
from the target application. It is an input to test generation, not a Test Hub test asset by
itself. A useful smartshot normally preserves some combination of:

- the application URL, page or route, and capture context;
- an ordered sequence of user actions such as open, click, type, select, submit, and assert;
- observed element identity, such as semantic labels/content, attributes, DOM snippets, or
   locators;
- captured values, screenshots, timing/state information, or notes that help explain the action;
- optional grouping or scenario metadata that indicates where one workflow starts and ends.

The exact file extension, directory, and field names are repository-specific and must be learned
from the artifacts found in the target repository. Do not call a screenshot alone a smartshot
unless it also carries actionable interaction evidence. Do not treat a smartshot as proof that a
locator still works: check its target URL and state, then live-verify incomplete, ambiguous, or
stale evidence before emitting a DSL step. Preserve the source path and confidence in
`LIVE-NOTES.md` so later fixes can distinguish recorded evidence from live observations.

Smartshots are evidence, not permission to invent DSL fields or selectors. When translating one,
map only fields supported by `reference/dsl-guide.md` and the schemas. Preserve the evidence's
page transitions and data values as variables where appropriate, omit recorder-only metadata, and
live-verify any selector that is missing, ambiguous, stale, or inconsistent with the target
application. Record the provenance in `LIVE-NOTES.md`, including the smartshot path and which
steps were confirmed live versus translated from the artifact.

Classify evidence before using it:

- **Confirmed**: a fact in `LIVE-NOTES.md` that still matches the target, or a selector observed
   live in this session.
- **Recorded**: a selector/action translated from a smartshot or existing module but not live
   rechecked in this session.
- **Uncertain**: missing, stale, ambiguous, or conflicting evidence.

Recorded evidence is acceptable for low-risk, already-covered flows when the user chooses the
smartshot route. Uncertain evidence must be live-checked before authoring the step. Authentication,
checkout, destructive admin actions, and module seams are high-risk: live-check them even when
smartshots exist, unless a current TestHub result already confirms the exact composed flow.

## Generating a test — browser- or smartshot-grounded

**Do not generate new test steps by recombining or pattern-matching against unrelated tests in the
repo.** Every new selector must be either confirmed live, supported by a usable smartshot chosen
by the user, or explicitly marked for live verification before publication. Copying selectors from
an unrelated test produces a plausible-looking test that may not match the real page. Whole-module
reuse via `run:` remains the right way to avoid re-authoring a known-working flow.

This skill targets **test/staging instances, not production** — interact with the live app
freely (sign up, submit forms, click admin actions), the way a real tester would on a disposable
environment, without pausing to ask permission for each routine action. Only pause if the target
URL genuinely looks like production rather than a test/demo instance.

Before writing anything, the inventory-and-decide-once pass above should already have resolved
these items. Ask a single batch only for whatever remains unknown:

1. **Target application URL** — unless already known from an existing `.dtc.yaml` in the
   component folder (or if there's more than one plausible environment — dev/staging/prod, ask
   which).
2. **Target repo and component** — which git-backed test repo the artifacts should be written
   into, and the component name to create (new) or place the tests under (existing). This
   determines the component folder (`<repo>/<Component>/`) everything else below is relative to.
3. **What the test(s) should cover** — which page(s)/flow/feature, if not already described.
4. **Modules or inline steps** — whether reusable flows (sign-in, sign-out, checkout, etc.) for
   this component should be factored into a `modules/` subfolder and invoked via `run:`, or
   whether to write fully inline steps instead. Skip asking if the component already has a
   `modules/` folder (or clearly doesn't need one because the request is a single simple flow) —
   otherwise ask once, up front, since it shapes how everything gets structured.
5. **Check for `<repo>/<Component>/LIVE-NOTES.md`** and trust what it already confirms; this is
   an inspection action, not normally a user question.
6. **Generation route** — if usable smartshots were found, ask whether to generate from them,
   use agent-driven browser discovery, or use a hybrid. Skip this question when the user already
   chose a route or no usable smartshots exist.
7. **Drive the real browser through whatever's left, efficiently** — batch each logical
   page-interaction into one tool call (e.g. one JS-execution call to fill and submit a whole
   form) rather than one call per click/type, and prefer JS-based queries over screenshots for
   verifying what happened. See `reference/dsl-guide.md`'s "Efficient browser driving" section —
   it also documents concrete pitfalls (stale refs, hidden-pane click failures, rendered-vs-raw
   text case) worth avoiding rather than rediscovering.
8. **Capture each element's real `object` and identifying properties from the live DOM** as you
   go, before translating that interaction into a DSL step.
9. **Verify the seam between composed pieces live** — especially across a `run:` module
   boundary — and if the page after one piece doesn't match what the next assumes, bridge it with
   a real, confirmed in-app navigation `click:`. **Do not "fix" a page-state mismatch with a
   second `open:` to the same window** — that reloads a single-page app and already broke a
   composed test in this project. The DSL itself does allow multiple `open`s (the product samples
   use them for named windows/tabs via `context`/`attach`, and a verified deep link is legitimate
   on a server-routed app), so the rule is about *what the reload does to the app*, not about
   `open` count. See `reference/dsl-guide.md` → `open`.
10. **Reach for the flow steps the DSL actually has.** Anything that may or may not be present
   (consent banners, first-run dialogs) goes inside an element-form `if` with a bounded
   `stepTimeout`, never a hard `click`. Anything load-dependent is guarded by an element `verify`
   or `wait` with an explicit `stepTimeout`, never a fixed `wait: 2s`. Read the live app's real
   load time before choosing the timeout.

Then follow the rest of the step-by-step workflow at the end of `reference/dsl-guide.md`: if the
user opted for modules, inspect existing candidates during the inventory pass and **ask once**
(covering every candidate) whether to reuse them via `run:` or write fresh steps. Do not ask again
after the decision gate. Group steps into `with:` blocks per
page/interaction, prefer semantic element properties (`content`, `label`, `src`) over raw
`xpath`, omit the recorder-only `shot` field, and parameterize credentials/URLs/test data as
`vars`. Afterward, **update `LIVE-NOTES.md`** with anything newly confirmed.

Write the generated files into the target repo/component gathered above, following the existing
naming and folder conventions in that repo (`.dtc.yaml`, `.dtx.yaml`, `.dts.yaml`, `.ddf`,
`.cgen`). If it's a new component, create its `.dtc.yaml` (with the target URL) and, only if
modules were opted into, a `modules/` subfolder.

## Choose the push destination deliberately

Before the first commit/push in a session, use common sense to decide whether the change belongs
on a temporary branch or `main`:

- Use a **temporary branch** for new or experimental generated tests, a dry run, uncertain
   selectors, work that still needs Test Hub execution, or any request framed as a proposal/review.
- Use **`main`** when the user explicitly requests it, the repository workflow clearly treats
   `main` as the normal direct-push branch, or the user has already established that preference for
   this session.
- If both are plausible and the user has not established a preference, ask once: **“Should I push
   this to a temporary branch or to `main`?”** Include the proposed branch name when suggesting a
   temporary branch.

Remember the user's choice for subsequent pushes in the same session and follow that pattern unless
the user tells you otherwise. Do not silently switch an established temporary-branch workflow to
`main`, or vice versa. A temporary branch should use a descriptive name such as
`copilot/senditcycles-smoke-tests`; check the current branch and avoid reusing an existing branch
without confirming its purpose. Report the destination branch and commit after pushing.

**After committing and pushing**, check whether `testhub__*` tools are connected this session
(see `reference/testhub-mcp-tools.md`) — but expect the normal case is that they aren't. If they
are connected, use them first for project/asset discovery and for reviewing executions the user
has already run. Execution is optional because `run_test` may be unavailable or may reject
OAuth-only authentication when a refresh token is required.

- **If connected and execution is authenticated**: optionally run the generated test(s) and close
   the loop yourself — run, fetch the real result, and if it failed, diagnose and fix using the
   actual step-level failure detail (never guess), then re-run to confirm. Query only the selected
   asset(s), branch, and relevant commit/version where the tool supports those filters. See
   `reference/testhub-mcp-tools.md`'s "Fix-and-rerun loop" for the bounded workflow. Report the
   final real outcome to the user (pass, or fail with concretely what's still wrong and why you
   stopped iterating).
- **If execution is unavailable or rejected because a refresh token is required**: report that
   limitation without treating it as a test failure. Ask the user to run the test(s) in Test Hub,
   then use `testhub__get_results` and `testhub__get_result_by_id` (and screenshots when available)
   to review the user's real execution. Match results to the project, branch, asset, and commit or
   start time rather than relying on the newest result globally. If a read-only MCP call returns
   `401`, retry once; if it still fails, stop probing and report an MCP authentication outage.
- **If not connected**: tell the user the generated test needs a real run in Test Hub, since this
  session's browser is a different engine from Test Hub's own runner. When they come back with a
  result (a screenshot, a description of what failed), treat that the same way as any other live
  finding — read the actual failure detail, say concretely what it does and doesn't rule out, and
  be explicit about whether a proposed fix is confirmed or still a guess.

This loop is not a fallback to tolerate; it's worked well in practice and should be treated as the
normal way this skill's output gets verified — automatically when the tools are there, manually
via the user when they aren't.

## Validating output

Before treating generated YAML/JSON as done, run this focused gate:

1. Parse every touched file with a real YAML parser, then check each step is a mapping with
   exactly one action key (`note`/`stepTimeout`/etc. belong *inside* the action — a sibling
   `note:` or a drifted indent is a second key and fails the schema), then validate against the
   relevant schema in `reference/schemas/`. Every object in this DSL uses
   `additionalProperties: false`, so a made-up or misspelled field will be rejected by DevOps
   Test Hub even when it looks plausible. An indentation-only regex check is not sufficient.
2. Confirm every `run:` path resolves, every suite entry exists, every referenced component has a
   `.dtc.yaml`, and every generated test uses the intended target URL/profile.
3. Check that selectors are classified as confirmed, recorded, or uncertain; no uncertain selector
   is published without live verification or an explicit user choice to accept recorded evidence.
4. Check credentials and tokens: passwords belong in an environment file (`.dte.yaml` `users`
   with `type: secret`, consumed via `${user('password')}`) or a `type: secret` var — never as a
   literal in a `.dtx.yaml`. Never put MCP/offline tokens in generated files or chat, and avoid
   copying real personal credentials into reusable tests.
5. Run the cheapest available executable check for the touched slice, then `git diff --check`.
   Inspect the final status to ensure unrelated user changes are neither staged nor overwritten.
6. After pushing, use TestHub asset discovery to confirm the expected names, branch, and commit are
   visible before attempting execution or result review.
