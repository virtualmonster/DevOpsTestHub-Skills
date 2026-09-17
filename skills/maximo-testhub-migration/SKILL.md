---
name: maximo-testhub-migration
description: Migrate Maximo Test Automation Framework browser UI tests into HCL DevOps Test Hub browser DSL. Use when converting Maximo Java/TestNG/Selenium assets, .bin recorder tests, page objects, or UI smoke packs into .dtc.yaml, .dtx.yaml, .dts.yaml, and data assets. Exclude REST, OSLC, API, database, and desktop tests unless explicitly requested.
---

# Maximo to DevOps Test Hub UI Migration

Migrate only the browser UI subset of the IBM Maximo Test Automation Framework into native HCL DevOps Test Hub browser assets. This is a translation workflow, not a Java/TestNG importer.

## Authorization and question policy

When the user explicitly authorizes the migration, treat that authorization as approval for routine read-only inspection, archive extraction to temporary storage, repository cloning, browser interaction against the named test/staging environment, asset generation, validation, commit, and push using the established branch pattern. Do not ask permission again for each read or routine tool call.

Batch routine work aggressively: combine inventory reads, group related asset generation, run one
focused validation pass, and use one publish operation. Do not add agent-authored approval prompts
for individual files or commands. Host-level VS Code, MCP, browser, or terminal security dialogs
may still appear; a skill cannot suppress those controls.

Ask one batched question only when a required input is missing or materially ambiguous, especially:

- Maximo application URL when the source contains only a placeholder;
- TestHub project/component or target repository when not already clear;
- credentials or offline tokens, which must never be requested in chat;
- a production-looking target;
- destructive application actions or overwriting unrelated user work;
- whether to publish to a temporary branch or `main` when no session preference exists.

Reuse the user's answers for the rest of the session. Treat "keep going", "assume all actions are allowed", or equivalent wording as permission to continue routine work without repeated approval prompts.

## Migration boundary

Include:

- Selenium browser UI flows;
- Maximo login and navigation;
- recorder `.bin` flows whose interactions can be grounded in source or live DOM evidence;
- page-object actions translated into TestHub selectors and steps;
- UI screenshots and expected visible states;
- UI test data that can be safely parameterized.

Exclude by default:

- REST, OSLC, Maximo API, and API framework tests;
- JDBC/DB2/Oracle/database setup or verification;
- Java/TestNG listeners and custom Java reports;
- framework binaries, JARs, WebDriverManager, and Java helper classes;
- CI/build scripts unless the user explicitly asks for pipeline integration.

## Workflow

1. Inspect the source archive or repository read-only in one batch. Inventory `.bin` files, Java UI tests, page objects, TestNG suites, properties, data, screenshots, and API/database folders.
2. Select scope from the user's wording. For a smoke/spike request, select a small slice. For “the rest,” “all feasible,” “dozens,” or a bulk request, migrate the whole feasible browser UI batch rather than applying the small-slice default.
3. Confirm the Maximo URL. If the source uses `http://host:port/maximo` or another placeholder, create a configurable component only after the user supplies the real URL; never invent one.
4. Ground selectors. Use source locators only as candidate evidence. Live-verify high-risk or ambiguous Maximo selectors in the target app. Preserve source paths and evidence status in migration notes.
5. Generate native assets:
   - `.dtc.yaml` for the Maximo web component;
   - `.dtx.yaml` for each independent UI test or module;
   - `.dts.yaml` for a smoke suite;
   - instance-specific seeds (record IDs, sites, orgs, meter names) in `data/<env>/seeds.csv`,
     one row per environment, bound with `configuration: {dataset: data/${MAXIMO_ENV}/seeds.csv}`
     and `type: column` vars, so a customer swaps data rather than YAML. Verify every seed value
     against the target instance (read-only `mxapi*` GETs from an authenticated browser work well:
     `mxapiassetmeter?oslc.where=active=1` for metered assets, `mxapiwodetail` for editable work
     orders) and record the evidence in the data README. Keep `.ddf`/`.cgen` generators for
     synthesised values only.
6. Translate TestNG behavior deliberately. Use `concurrent`/`sequential` only where tests are independent or stateful. Do not carry over shared/static WebDriver state.
7. Move credentials to TestHub secret-backed variables or environment configuration. Never copy source passwords into generated assets.
8. Validate schemas, suite paths, `run:` references, target URLs, and `git diff --check`.
9. Commit and push according to the established branch policy. Report source-to-target mappings and excluded assets.
10. If TestHub tools are connected, discover the pushed assets and review execution results. Use detailed logs and screenshots for repairs; summaries alone do not justify changing selectors.

## Bulk migration mode

For a bulk request, “feasible” includes browser UI flows with documented prerequisites. Migrate
recorder assets that require a Maximo application, existing record, lookup dialog, callout
parameter, or manual seed when their interactions can be represented in TestHub steps. Exclude
only API, REST, OSLC, database, desktop, framework-internal, and genuinely untranslatable assets.

For every migrated asset, preserve source path, required application/record context, parameters,
and limitations in a batch inventory document. Group the output by application area and create a
separate suite or suites. Report migrated, excluded, and deferred counts. A bulk request should
produce a substantial batch, not only a few representative examples.

Before publishing, run a structural smoke check on every generated `.dtx.yaml`:

- `steps:` is followed by a list whose top-level entries all have identical indentation;
- `open`, `run`, and `with` are sibling entries, never nested under one another;
- `open` is first and appears at most once;
- every `run:` path resolves relative to the test file;
- modules contain no `open:` and declare every interpolated variable in their own
   `configuration.vars`;
- quoted JS expressions such as `${Date.now()+'-suffix'}` use YAML-safe outer double quotes.

Do this structural check after formatter/editor changes as well as before commit. A file can look
visually plausible while TestHub rejects it because one list item has drifted by two spaces.

Reusable module variables must be declared inside the module itself. For example, the Maximo login
module must declare `Maximo_User` and `Maximo_Password` in its own `configuration.vars` before
referencing `${Maximo_User}` or `${Maximo_Password}`. A caller may override those values, but a
caller-only declaration is insufficient for TestHub editor and runtime resolution.

When the Maximo MAS login route presents a cookie banner, inspect the same environment that will
execute the TestHub asset before authoring the selector. The local browser and TestHub execution
pod can render different TrustArc variants. In the local browser, the main IBM banner exposed
`button#truste-consent-required` (`Required only`); in the execution pod, the confirmed recorder
evidence exposed an `html.span` with rendered content `Accept All` and smartshot
`../IBM Maximo Application Suite_2daw5f.dti.jpeg#344`. The `.close` anchor observed locally belongs
to a secondary hidden domain-list popup and is not a universal banner selector.

Prefer the execution-pod smartshot/semantic evidence when it exists. Keep cookie handling in a
reusable no-`open` module and compose it after the login module when the banner appears only after
authentication. Do not assume a selector captured in the interactive browser is valid in the
TestHub execution pod; treat each browser environment as separate evidence.

## First-pass reliability rules

Apply these rules to every MAS browser migration before its first TestHub run. They are based on
live MAS and execution-pod evidence, but the target environment and account still determine which
applications, records, and controls are available.

### YAML and TestHub DSL

- Parse every touched `.dtx.yaml` with a real YAML parser in addition to structural checks. A
   top-level indentation checker will not catch malformed child mappings. The target repository
   carries `scripts/validate_maximo_dsl.py` (PyYAML): real parse, one-action-key-per-step, `open`
   first/unique, no `open` in modules, `run:`/suite paths resolve, structured property values,
   every `${Var}` declared locally, no stray whitespace in var values, no placeholder component URL.
   Run it before every commit; the PowerShell wrapper `Validate-MaximoDsl.ps1` delegates to it.
- A step is a mapping with **exactly one** key (schema `Step.maxProperties: 1`); `note`,
   `stepTimeout`, `shot` go inside the action object, never beside it.
- Credentials: never literal. Declare `Maximo_Password: {type: secret}` (or use a `.dte.yaml`
   `users` entry and `${user('password')}`) and let the Test Hub environment supply it. The URL
   belongs in `.dtc.yaml` / one shared var, not duplicated per test — a trailing-space typo once
   propagated into 21 files that way.
- Use two spaces for every top-level `- open:`, `- run:`, `- with:`, `- click:`, and `- wait:`.
   `object`, `identifiers`, `properties`, and a structured value are nested two spaces at each
   level. Re-read the file after editor or visual-editor formatting; it can shift a new sibling
   under the preceding `run:` or `with:`.
- Quote XPath values containing `:` or other YAML-significant characters. For example:

   ```yaml
   - xpath:
         - val: "//span[contains(@id,'_tdrow_[C:1]_ttxt-lb[R:0]')]"
   ```

- Use the item-list form for **every** property value (`visible: [- val: 'true']`,
   `content: [- val: X]`, `id: [- val: X]`), never a scalar. The target server runs schema
   **2026/05** (`GET /test/content/schemas/script.json`), which has no scalar `Field` form and no
   bare-string `verify`; `run: out:` targets must be `{}`/lists, not names. Check the `$id` of any
   new server before authoring; the validator enforces these forms.
- Before diagnosing any failure, read the report's **Git line**: Test Hub project 6450 has three
   repositories connected (internal `MaximoPerfTests` with a stale `stu` branch, GitHub
   `Migrated-Maximo-Test-Framework`, GitHub `MaximoSamples`) and same-named assets are ambiguous.
   The step `Metadata` link is Test Hub's element dump (`exist/visible/reachable/proxyName`);
   `proxyName` is the `object` suffix.
- Run path resolution, YAML parsing, `git diff --check`, and a TestHub execution for every new
   module composition. A module that validates independently may still fail at its caller boundary.

### Login and cookie banner

- Login page controls confirmed live (2026-09): `input#jg772` (`html.inputtext`, username),
   `input#endng` (`html.inputpassword`), primary button `//button[contains(@class,'cds--btn--primary')]`
   (label "Log in"; the class qualifier correctly excludes the password-visibility toggle, which is
   also a `cds--btn`). These are MAS-generated IDs — valid today, brittle across upgrades.
- The URL chain is `home.<env>` → `auth.<env>/login/#/form` (authentication) → `masdev.home.<env>`
   (Suite navigator) → `masdev.manage.<env>/maximo/oslc/graphite/manage-shell/...` (Manage apps).
   Keep the `open` URL on the `home` host; record the others in `LIVE-NOTES.md`.
- **The TrustArc banner is per browser profile, not per login.** A warm profile shows no banner at
   all (confirmed live: TrustArc script loaded, no `truste-consent-required`, no `Accept All` span);
   a clean execution pod does show one. Therefore the dismissal must be **conditional**, never a
   hard `click` — a hard click fails whenever the banner is absent, which is the observed
   "cookie step fails only sometimes" symptom. Use the element-form `if`:

   ```yaml
   - if:
       note: TrustArc consent appears only on a clean browser profile
       object: html.span
       identifiers: [{ properties: [{ content: [{ val: Accept All }] }] }]
       stepTimeout: 8s
       steps:
         - click:
             object: html.span
             identifiers: [{ properties: [{ content: [{ val: Accept All }] }] }]
   ```
   Add a second `if` for the `button#truste-consent-required` (`Required only`) variant if the pod
   ever presents it; both variants coexisting harmlessly beats guessing which one runs. The
   recorder has also captured `html.button` content `Accept all` (lower-case) and
   `//img[@id='truste-consent-close']` on this instance (MaximoSamples, 2026-03) — the banner's
   markup varies by TrustArc version, so keep every variant guarded, never a hard click.
   Confirmed on the execution pod 2026-09-17: the `Accept All` span click passed.
- Keep dismissal in one no-`open` module composed after login. An element `wait` or `verify`
   must carry an explicit `stepTimeout` (one runner reported `duration is null` without it).

### MAS navigation

- **Translate `gotoApp("<alias>")` as a direct application load, not as menu clicks.** MAS Manage
   honours `…/maximo/oslc/graphite/manage-shell/index.html?event=loadapp&value=<alias>#/main` on
   the `manage` host, and the `value` is exactly the source framework's app alias (`asset`,
   `wotrack`, `bboard`, `action`, `calendr`, `collection`, `change`, `assetcat`, `intsrv`,
   `intobject`, `plusdasstr`, …). Confirmed live for `asset` (via the navigator) and `wotrack`
   (opened directly while authenticated): `document.title` and the in-frame app header became the
   application name and `quicksearch`/`toolactions_*` were present. This is a literal 1:1
   translation of `sendEvent("changeapp", …)` and scales to every recorder asset without per-app
   DOM archaeology.
- **Verify, don't wait.** A cold Manage app load took ~26 s live; a fixed `wait: 2s` guarantees
   "Object not found" on the first recorder step. After loading an app, assert arrival with an
   element `verify` (or `wait`) carrying a generous `stepTimeout` (start at `60s`) on a stable
   in-app control — the app header text, or `input#quicksearch` for list apps — and only then run
   recorder IDs.
- **`open` placement.** The convention is one `open` per test. Two precedented shapes for reaching
   an app: (a) make the deep link the test's single `open`, then run the login module if MAS
   redirects to `auth.<env>` — *whether MAS returns to the requested app after authentication is
   still unverified; test it deliberately (log out, open the deep link, log in) before adopting*;
   (b) `open` the home host, log in, then `open` the deep link with `context: <name>` and run the
   remaining steps under `with: {context: <name>}` — the product samples use named-context `open`s
   for additional windows that share the session, but confirm on this app in Test Hub before
   relying on it. Never re-`open` the same window mid-test.
- **Side-navigator clicks are the fallback, not the default**, and only in the nested form:
   `Open menu` → expand each parent group → click the child link, then verify arrival. Live facts
   (2026-09): the navigator is `nav.cds--side-nav`; groups are `button[aria-expanded]` under a
   default-expanded `Manage` group (a latent dependency); leaf links are `a[data-testid=
   sideNavMenuItem_<ALIAS>]`. **All 383 leaf anchors are in the DOM at all times but collapsed
   groups render them with `max-height: 0; visibility: hidden` — a locator finds them, a real click
   lands on a different application** (measured with `elementFromPoint`: `CALENDR` → "Asset
   Templates", `BBOARD` → "Assets (T&D)"). Never target a `sideNavMenuItem_*` anchor without
   first expanding its group and confirming interactability. Several `data-testid`s are duplicated
   (`ACTIVITY`×5, `MAIN`×5, `RELATION`×3, `COLLECTION`×2, `INTOBJECT`×2) — add `position` or a
   stronger anchor when you must use one. Confirmed group paths: Administration → Calendars /
   Classifications / Bulletin Board / Collections; Assets → Assets / Assets (T&D); Change → Changes;
   Integration → Enterprise Services / Object Structures; Work Orders → Work Order Tracking;
   System Configuration → Platform Configuration → Actions.
- **The classic Maximo UI is inside `iframe#manage-shell_Iframe`** (`/maximo/ui/…`). Every
   recorder ID (`toolactions_INSERT-tbb_image`, `quicksearch`, `m73f28d7-tb`, …) lives there;
   the top document has none. Test Hub resolves elements through frames without a switching step
   (product sample `frames/nested-frames.dtx.yaml`), so ordinary steps work — but a probe that
   finds "no controls" from the top document is looking in the wrong place. The rich-text editor is
   a frame *inside* that frame and remains unsupported for `type`.
- **Reachability, not just presence — and object type must match the tag** (both cost a first
   pilot run, 2026-09-17). A recorder ID captured with a live JS `.click()` can be *present and
   visible but not reachable* for a real Test Hub click: the left "Common Actions" nav on a record
   places options far down the iframe (e.g. `m74daaf83_ns_menu_METREAD_OPTION_a` "Enter Meter
   Readings" at ~y1154) and Test Hub does not scroll the iframe's inner viewport to them — the click
   times out and fails. Bring the target into view first via a reachable control (activating the
   **Meters** tab moved that option to ~y499), and prefer directly-editable in-dialog cells (the
   Enter Meter Readings dialog's New Reading column `m114fece6_tdrow_[C:2]_txt-tb[R:0]`) over an
   off-screen filter/View-Details path. Verify `document.elementFromPoint` on every recorder click
   during grounding. Separately, set `object:` to the real tag: Maximo controls whose id ends `_a`
   are `<a>` (`html.a`), not `html.button` (`m524afe2e_..._addrow-pb_addrow_a` "New Row" failed as
   `html.button`); the toolbar app-name `toolbar2-chld_appName` is a `<table>` (`html.table`), and a
   `verify`/`assign` with no `object:` at all resolves to nothing ("Verify undefined … Object not
   found") even when the element is plainly there.
- **Diagnose runs from the results REST API, not just the PDF** (works from a browser logged into
   the Test Hub server): `GET /test/rest/projects/{id}/results/{resultId}/data/views/functional/
   summary/` gives per-step verdicts and stepStatistics; each failing step in the report links a
   `Metadata` bucket (`…/data/buckets/{b}/items/{i}/content`) that is Test Hub's own element dump
   with `exist/visible/reachable/proxyName/content` at failure time — read it before changing a
   selector. Confirm the run's `Git` line (repo/branch/commit) first; project 6450 has three repos
   connected and same-named assets are ambiguous.

### Record context and Maximo dynamic controls

- Treat a recorder step that operates on a tab, Common Action, meter, or work log as requiring a
   selected record. Application list pages commonly start with `0 - 0 of 0`, even with no visible
   active filter; a “first row” selector alone is not a setup strategy.
- Prefer an application-specific reusable module that first `verify`s `input#quicksearch` is
   present (this doubles as the app-loaded gate, `stepTimeout: 60s`), types the supplied/declared
   seed identifier, uses `press: enter` (or clicks `quicksearchQSImage`), then `wait`s for the
   result row before clicking the first record-column control. Record-column controls observed in
   MAS are dynamic `span` elements with IDs like `_tdrow_[C:1]_ttxt-lb[R:0]` and `mxevent='click'`.
- Keep seed record IDs as module variables, not hard-coded assumptions. Verify them against the
   execution account before first run. An asset used for meter reading must have a configured
   meter; a work-order/activity seed must be editable by the automation account.
- The record context changes what is visible: after selecting an asset, `Enter Meter Readings`
   appears; after selecting a work order, the original `Log` tab and `New Row` work-log control
   appear. If those controls remain absent, report an entitlement/seed-data blocker rather than
   changing the recorded selector blindly.

### Rich-text editors and result repair

- Do not use a `type` step against a Maximo `*-rte_iframe`. TestHub resolves the iframe but its
   WebDriver action calls `clearElement`, which fails with `InvalidElementStateException`; the DSL
   has no frame-switching step. Preserve required non-iframe fields and omit optional rich-text
   body content, or defer the scenario if that content is required.
- Diagnose each failed run from detailed step data and Smartshots, not verdict totals. Distinguish
   `Object not found` on a post-navigation recorder action (usually missing record context) from a
   selector that resolves but cannot be interacted with (element-type/DSL limitation).
- Capture the execution revision, test name, failed step, object, structured locator, reason, and
   preceding passed steps in migration notes. Do not infer a selector replacement from a summary
   that omits those fields.

The original framework's `TpaeBrowser.gotoApp()` is one logical navigation event implemented as
`sendEvent("changeapp", currentApp, nextApp)`, followed by waits for the target application and
loading state. It is not inherently a chain of visible menu clicks. When translating `gotoApp` to
TestHub, use a live-grounded side-navigation module only as the browser equivalent, and verify the
target application has loaded before the source recorder IDs are used. A click-only module without
a post-navigation wait/verification is incomplete.

## TestHub compatibility rules

Use the structured field-value form for every element property, including Maximo IDs:

```yaml
properties:
   - id:
         - val: jg772
```

The scalar form `id: jg772` is rejected by some Test Hub visual editors because the field expects
an item array or expression object. Apply the same rule to `xpath`:

```yaml
properties:
   - xpath:
         - val: //button[contains(@class,'cds--btn--primary')]
```

Keep the initial migration suite minimal:

```yaml
tests:
   - Maximo Login Smoke.dtx.yaml
```

Suite `configuration` (`concurrent`, `sequential`, `profiles`, `stepTimeout`, `vars`) is
schema-valid and used throughout the vendor's own samples, but one Test Hub server/editor version
in this project rejected it. A suite with only `note` and `tests` is the most portable form; add
configuration once the target server has been seen to render it.

The scalar property shorthand (`id: jg772`) is likewise schema-valid and is what the vendor
samples use; the structured form above is a compatibility choice for the visual editor version
that rejected the shorthand. Both parse; the structured form is never wrong.

## Source mapping rules

| Maximo source | TestHub target |
| --- | --- |
| `TestRelogin.bin` login/relogin events | `.dtx.yaml` login/relogin test |
| Java `LoginPage` / browser wrapper | grounded `click`/`type`/`verify` steps or a new module |
| TestNG XML suite | `.dts.yaml` suite |
| `.properties` URL/browser settings | `.dtc.yaml` URL and `configuration.profile` |
| `gotoApp("<alias>")` / `sendEvent("changeapp", …, "<alias>")` | direct app load: `<manage-host>/maximo/oslc/graphite/manage-shell/index.html?event=loadapp&value=<alias>#/main` (same alias), then an element `verify` on the loaded app header |
| CSV/JSON test data | `.ddf`/variables where supported |
| custom Java listener/report | TestHub execution result and screenshot review |
| REST/OSLC/JDBC classes | excluded from this browser migration |

## Stop conditions

Stop discovery and generate when the selected smoke flow, target repository/component, target URL,
selector evidence, credential strategy, and suite shape are known. Do not enumerate or translate
unrelated API/database assets.

Stop migration and report a blocker when the target URL is still a placeholder, the selected flow
has no trustworthy selector evidence, or the source requires a framework behavior with no known
TestHub DSL equivalent.
