# HCL DevOps Test Hub — Browser/UI Test DSL Guide

Task-focused reference for writing browser/UI test artifacts for DevOps Test Hub. Sources of
truth, in order of authority:

1. **The JSON Schemas** in `schemas/` (draft-07, `$id` version `2026/07`). Every object uses
   `additionalProperties: false`, so an unknown or misspelled key is rejected outright.
2. **Product-authored samples** in `samples/` — a curated subset of the vendor's own test corpus
   (the `onetest-server` `lang/samples` tree). These are the runtime's *unit tests*; a construct
   that appears there is known to execute.
3. **`../examples/CycleStore/`** — a worked component showing repository layout conventions.
4. **Project observations** — things seen in real Test Hub runs on specific server versions.
   These are marked as such below; they can be version-specific.

Evidence tags used in this guide: **[schema]**, **[sample: path]**, **[project run]**,
**[live DOM]**. Prefer a construct with a sample behind it; flag anything you can only justify
from the schema.

Scope: browser testing. The same DSL also covers API (`send`), SQL (`sql`), stubs (`.dtv.yaml`),
messages (`.dtm.yaml`), transports (`.dtt.yaml`) and load profiles (`.dtp.yaml`) — those files
exist in `schemas/` for completeness but this skill does not generate them.

## File types and extensions

| Extension | Artifact | Schema | Purpose |
|---|---|---|---|
| `.dtc.yaml` | Component | `component.json` | The app under test. Keys: `note`, `meta`, `url`, `icon`, `type: web`, `dependencies`. One per component folder, literally named `.dtc.yaml`. |
| `.dtx.yaml` | Test / Module | `script.json` | A script. Tests and reusable modules share the format; a module is just a script invoked via `run:`. |
| `.dts.yaml` | Suite | `suite.json` | Ordered (or concurrent) list of tests/suites, with optional suite-level `configuration`. |
| `.dte.yaml` | Environment | `environment.json` | Named `users` (credentials as secrets), `vars`, browser/agent `profiles`, `includes`. **This is where credentials belong.** |
| `.csv` (+ `.csv.metadata`) | Dataset | n/a | Header row = variable names. The `.metadata` XML sidecar is tool-generated; don't hand-author it. |
| `.ddf` / `.cgen` / `.category` | Generated data | JSON | Data-definition files and generators (see CycleStore). Not present in the product corpus, which uses CSV throughout. |
| `.dti.jpeg` / `.dti.json` | Smartshot pair | n/a | Recorder screenshot + DOM snapshot, referenced by `shot: <file>.dti.jpeg#<offset>`. Optional; never fabricate one. |
| `.dtv` / `.dtm` / `.dtt` / `.dtd` / `.dtp` | Stub / Messages / Transport / DB query / Load profile | respective schema | API/perf side of the DSL; out of scope here. |

## Anatomy of a script (`.dtx.yaml`)

```yaml
note: Human-readable description
configuration:
  profile: edge                      # or chrome | firefox | safari | edge+medium.phone | {name, capabilities}
  stepTimeout: 30s                   # default per-step timeout
  vars:
    APP_URL: https://app.example.test/
    Username: {}                     # IN variable, no default — caller/environment supplies it
    _Password:                       # secret-backed: never a literal
      type: secret
    RESULT:
      modifier: out                  # returned to the caller
steps:
  - open:
      url: '${APP_URL}'
  - with:
      note: Sign in
      steps:
        - type: { object: html.inputtext, identifiers: [{ properties: [{ label: Username }] }], value: '${Username}' }
```

Root keys **[schema]**: `enabled`, `note`, `configuration`, `meta`, `steps`, `emulate`.
`configuration` keys: `meta`, `cache`, `dataset`, `stepTimeout`, `profile`, `vars`.

**A step is a mapping with exactly one key** — the action **[schema: `Step.maxProperties: 1`]**.
`note`, `enabled`, `stepTimeout`, `shot`, `meta`, `hooks` go *inside* the action object:

```yaml
- click:
    note: Save the record          # correct
    object: html.button
    identifiers: [...]
```

A `note:` written as a sibling of the action key is a second key and fails the schema. This is
also the shape a drifted indent produces, so a real YAML parse plus a one-key check catches
most structural breakage.

## Variables and expressions

`${...}` is evaluated as JavaScript (Rhino) **[sample: modules-vars/variables.dtx.yaml]**.
`${COLOR.toUpperCase()}`, `${Date.now()+'-x'}`, `${i==6}` all work.

Declaration shapes in `configuration.vars` **[schema: `ModifiedVarDef`]**:

| Shape | Meaning | Evidence |
|---|---|---|
| `NAME: literal` | default value, implicitly `in` (overridable by caller/environment/dataset) | everywhere |
| `NAME: {}` | declared, no default; must be supplied | modules-vars/status.dtx.yaml |
| `NAME: {expr: ..., modifier: out}` | written by this script, visible to the caller | modules-vars/module.dtx.yaml |
| `NAME: {expr: ..., modifier: local}` | private to this script; a caller's same-named var is neither read nor overwritten | modules-vars/call-module.dtx.yaml |
| `NAME: {type: secret}` / `{expr: key, type: secret}` | pulled from the environment's secret collection | environment/env.dte.yaml |
| `NAME: {expr: COLUMN, type: column}` | bound to a dataset column (see Data-driven) | data-driven/pull-data.dtx.yaml |
| `NAME: {expr: ..., type: js}` | evaluated as JS — use for numbers, booleans, arrays, **functions** | modules-vars/var-types.dtx.yaml |
| `NAME: {expr: path, relative: 'true'}` | resolved as a path relative to this file | modules-vars/relative.dtx.yaml |

Rules worth knowing:

- **Every `${Var}` a script references must be declared in that script's own `configuration.vars`**
  (or arrive via `run: in:` / dataset / environment). Referencing an undefined variable is an
  error, not an empty string **[sample: logging/invalid-var-def — a var defaulting to
  `${UNDEFINED}` makes the whole script unreachable]**. Callers passing `in:` does not remove the
  module's own declaration requirement.
- Numeric-looking strings behave as numbers in JS: `ELEVEN: '11'` → `${ELEVEN + 1}` is `12`. Force a
  string with `${"11"}` **[sample: variables.dtx.yaml]**. Use `type: js` for real booleans/numbers.
- Names must be JS identifiers; `A B` is rejected **[sample: variables/bad-var]**.
- **Functions are variables**: `add_10: {expr: 'n => n + 10', type: js, modifier: out}` in a
  module, then `run:` it and call `${add_10(20)}` **[sample: modules-vars/functions.dtx.yaml,
  var-funcs.dtx.yaml]**. This is how to build a reusable helper library.
- Built-ins seen in the corpus: `${stub('http://name')}` (stub endpoint), `${user('username')}`
  / `${user('password')}` (current actor from the environment — see Environments),
  `${SYS_BASE_URI}` (this file's URI) and `${SYS_BASE_DIR_URI}` (its folder).
- `assign` mutates variables mid-flow: `assign: {vars: {j: '${j+2}'}}`. Read a value off an
  element into a var: `assign: {object, identifiers, properties: [{content: [{var: NAME}]}]}`.
- `cache: 'true'` on a module's `configuration` runs it once and reuses its outputs for later
  callers in the run **[sample: caches/*]**. Never cache a module that touches browser state — the
  corpus's own `invalid-cache.dtx.yaml` is labelled invalid for exactly that reason.

## Step catalog

Every entry in `steps:` is a single-key mapping using one of these **[schema: `Step`]**:
`open` `click` `type` `select` `press` `verify` `wait` `if` `while` `do` `iterate` `with`
`assign` `log` `fail` `run` `send` `sql`.

Common optional fields on most steps: `note`, `enabled` (JS; skip the step when false), `meta`,
`shot`, `stepTimeout`, `emulate`, `hooks: {end: {steps: [...]}}` (cleanup when the step's
scope ends **[sample: log/end-run.dtx.yaml]**).

### `open`

```yaml
- open:
    url: '${APP_URL}'
    stepTimeout: 60s
```

Fields **[schema]**: `url`, `attach` (JS), `context` (name), plus the common ones.

- **Convention vs rule.** In this project's own examples `open` appears once, first, per test —
  and a second mid-test `open` to the *same* window once broke a composed SPA test by reloading
  the app and losing state **[project run]**. That is a real hazard for single-page apps. It is
  **not** a DSL restriction: the product corpus has `open` as the third step, nested inside a
  `with` after a `run` and a `log` **[sample: frames/nested-frames.dtx.yaml and 13 others]**,
  two consecutive `open`s **[sample: fonts.dtx.yaml, open-twice.dtx.yaml]**, and four `open`s in
  one test **[sample: tabs-windows/multi-tabs.dtx.yaml]**.
- **Deep links.** For server-routed apps whose session lives in cookies, opening a specific
  entry URL directly is a legitimate way to reach a page — but treat it as a claim to verify
  live (does the app honour the URL when already authenticated? when not?), and never use it to
  paper over an SPA state mismatch. For SPAs, navigate with real in-app `click`s.
- **Windows and tabs.** `open` with `context: <name>` targets a *named* browser context; a later
  `with: {context: <name>, steps: [...]}` or `run: {url, context: <name>}` acts in it. When the
  app itself opens a new tab (target=_blank), attach to it:

  ```yaml
  - click: { object: html.a, identifiers: [{ properties: [{ content: Other }] }] }
  - open:
      note: attach to the tab the app just opened
      url: ${TEST_ENDPOINT}/other.html     # may be omitted: attach: 'true' + context alone also seen
      attach: 'true'
      context: newtab
  - run:
      url: trivial-tab-module.dtx.yaml
      context: newtab
  ```
  **[sample: tabs-windows/trivial-tab-run-context.dtx.yaml, multi-tabs.dtx.yaml]**. The default
  (unnamed) context continues to refer to the original window. Contexts share the browser
  session (cookies), which is what makes a second named `open` a *non-destructive* way to reach
  another URL while keeping the first window intact — precedented in the corpus, but confirm on
  the target app before relying on it.
- `meta: {browserName, browserVersion, platformName}` on `open` is recorder metadata; keep or
  drop, it is informational **[sample: recorder/test_ua.dtx.yaml]**.

### `click`

```yaml
- click:
    object: html.button
    identifiers: [{ properties: [{ content: Save }] }]
    use: click            # click | double_click | right_click | hover | drag | long_press
- click:
    object: html.div
    identifiers: [{ properties: [{ content: Drag me }] }]
    use: drag
    to:
      object: html.div
      identifiers:
        - offset: below   # above | below | left_of | right_of | (x,y)
          properties: [{ content: Item 1 }]
```

**[sample: controls/html-controls-ui.dtx.yaml, html-controls-drag-drop.dtx.yaml,
tabs-windows/multi-tabs.dtx.yaml]**. `use: hover` reveals menus/tooltips.

### `type`, `select`, `press`

```yaml
- type:
    object: html.inputtext
    identifiers: [{ properties: [{ label: 'Name:' }] }]
    value: '${NAME}'
    relative: 'true'      # append instead of replace (optional)
    nativeInput: 'true'   # send native key events (optional)
- type: '${USERNAME}'      # shorthand: types into the currently focused element
- select:
    object: html.select
    identifiers: [{ properties: [{ label: 'Country:' }] }]
    value: USA            # by visible option text
- press: enter            # enter | tab | ... ; object form: {key, modifiers: [ctrl|alt|shift|command], nativeInput}
```

The shorthand `type` after a focus check is the product's own login idiom
**[sample: recorder/login-only-ui.dtx.yaml]**: `verify` that `focus: 'true'` on the username
field, `type`, `press: tab`, `verify` focus on password, `type`, `press: enter`.
Multi-line values via a YAML block scalar are fine **[sample: controls/html-multiline.dtx.yaml]**.

### `wait`

```yaml
- wait: 2s                            # duration shorthand
- wait:                               # wait for an element (with matching properties) to appear
    object: html.inputtext
    identifiers: [{ properties: [{ label: 'Wait:' }, { content: '${expected}' }] }]
    stepTimeout: 30s
```

**[schema: `WaitStep` oneOf duration | element]**, **[sample: flow/wait-step-test.dtx.yaml,
api-record driver `wait: {object: html.body, stepTimeout: 2s}`]**. Always give an element-wait
an explicit `stepTimeout` — one project runner reported `duration is null` for an element wait
without one **[project run]**. Prefer element-waits over fixed durations for anything
load-dependent; a fixed `wait: 2s` before a 25-second app load is the classic cause of
"object not found" on the next step **[live DOM, Maximo]**.

### `verify`

Three forms **[schema]**:

```yaml
- verify: FOO_BAR_RESULT === 'MyFooMyBar'          # one JS expression
- verify:                                           # several JS expressions (all must hold)
    - i == 0
    - j == 10
- verify:                                           # element properties
    object: html.button
    identifiers: [{ properties: [{ content: Save }] }]
    properties:
      - enabled: 'false'
      - visible: 'true'
    stepTimeout: 60s
```

Element `verify` retries until the properties match or `stepTimeout` elapses **[sample:
scripts/ui/verify-no-match-timeout*.dtx.yaml exist precisely to exercise that]**, so **a
`verify` on a stable post-load control with a generous timeout is the idiomatic "wait until
the page/app has loaded" step** — better than a bare `wait`, because it also asserts you landed
in the right place. Assertable properties seen: `content`, `exist`, `visible`, `enabled`,
`focus`, `message` (dialogs), plus `regex`/`ends`/`includes` operators on `content`
**[sample: controls/html-controls-ui.dtx.yaml, assign-and-verify-non-existent-controls.dtx.yaml]**.
`exist: 'false'` with a short `stepTimeout` asserts absence without waiting long.
A JS `verify` can have side effects (`FOO_BAR_RESULT = FOO + BAR; true`) — the corpus uses it
that way, but prefer `assign` for clarity.

### `if`, `while`, `do` — conditional and optional steps

`if`/`while` take **either** a JS `condition` **or** an element (`object` + `identifiers`)
whose existence is the condition **[schema; sample: flow/flow-steps-test.dtx.yaml]**:

```yaml
- if:
    note: dismiss the consent banner only when it is actually shown
    object: html.button
    identifiers: [{ properties: [{ id: truste-consent-required }] }]
    stepTimeout: 5s                  # bounds the existence probe
    steps:
      - click:
          object: html.button
          identifiers: [{ properties: [{ id: truste-consent-required }] }]
- if:
    condition: CheckIfInputControlExists
    steps: [ ... ]
```

This is **the** pattern for anything that may or may not be present (cookie banners, first-run
tips, optional dialogs). A hard `click` on such an element fails whenever it is absent — which
is environment-dependent (consent is stored per browser profile, so a warm profile shows no
banner and a clean execution pod does) **[live DOM, Maximo]**. The alternative is `enabled:` on
the step with a JS expression.

To branch on existence without an element-form `if`, capture it first:
```yaml
- assign:
    object: html.inputpassword
    identifiers: [{ properties: [{ label: ThisControlDoesNotExist }] }]
    properties: [{ exist: [{ var: ControlExists }] }]
    stepTimeout: 1s
- if: { condition: '!ControlExists', steps: [ ... ] }
```
**[sample: controls/assign-and-verify-non-existent-controls.dtx.yaml]**.

`while` loops while its condition/element holds; `do: {steps, while: <js>}` runs at least once.
The corpus notes `content` conditions inside `while` should use `regex` because JS predicates are
not supported in that position **[sample note in flow-steps-test]**.

### `assign`, `log`, `fail`, `iterate`

- `assign` (see Variables) reads element properties (`content`, `exist`, ...), sets vars from JS,
  or pulls the next dataset row.
- `log: text` / `log: {note, hooks}`; `fail: reason` stops the script.
- `iterate: {dataset: a.csv, vars: {COL_A: {expr: COL_A, type: column}}, steps: [...]}` loops the
  nested steps once per row **[sample: data-driven/iterate.dtx.yaml]**.

### `with`

Groups steps, carries a `note`, and optionally switches `user` (environment actor) or `context`
(named window). Nearly every product sample wraps each page interaction in a `with`.

### `run` — composition

```yaml
- run: modules/Sign In.dtx.yaml                # string form
- run:
    url: modules/Search Record.dtx.yaml        # ${vars} and wildcards allowed
    in:
      Record_Id: '${Seed_Asset}'
      Unused: null                             # null = explicitly unbound
    out:
      RESULT: {}                               # same name in caller
      TOKEN: MY_TOKEN                          # rename
      BOTH: [A, B]                             # fan out to several caller vars
    dataset: seeds.csv                         # run once per row
    inline: 'true'                             # splice into caller scope instead of isolating
    context: newtab                            # run inside a named window
    profiles: [chrome]                         # suite-style profile filter
    enabled: MODULE === 'animals'              # conditional dispatch
```

**[schema: `RunStep`; samples: modules-vars/*, data-driven/5cols-parent.dtx.yaml,
datadriven-inline/framework.dtx.yaml]**. Semantics confirmed by the samples:

- A module's `in` vars (implicit default) take the caller's same-named value; `out` vars flow
  back; `local` vars are isolated **[sample: modules-vars/call-module.dtx.yaml + module.dtx.yaml]**.
- A failing module (a failed `verify`, a `fail`, an unresolved element) **aborts the caller** at
  that step — later caller steps do not run **[sample: modules-vars/modules.dtx.yaml]**. In a
  suite, the *next test* still runs **[sample: logging/suites-continue-after-error.dts.yaml]**.
- `run:` can target a `.dts.yaml`, a wildcard (`modules/*.dtx.yaml`), or a stub `.dtv.yaml`.
- A module has no `open` only by convention — it inherits the caller's window/context.

### Native dialogs — `window.*`

Alerts, confirms and prompts are first-class objects **[sample: controls/html-js-popups.dtx.yaml]**:

```yaml
- click: { object: window.ok }
- click: { object: window.cancel }
- verify: { object: window.popup, properties: [{ message: 'Press a button!' }] }
- type:   { object: window.popup, value: text for the prompt }
```

### `emulate`, `send`, `sql`

`emulate` (on `open`/`press`/root) replays recorded HTTP cascades for performance emulation;
`send` and `sql` are the API/DB side. All exist in `script.json`; none are browser-test tools.

## Frames

**No frame-switching step exists — and none is needed.** Element resolution looks through
`<frame>`/`<iframe>` boundaries transparently: the product's own test types into inputs three
framesets deep using nothing but `object: html.inputtext` and a `label` **[sample:
frames/nested-frames.dtx.yaml]**, and the controls sample types into an iframe-hosted form the
same way. Applications that render inside an iframe (e.g. MAS Manage's classic UI in
`iframe#manage-shell_Iframe` **[live DOM]**) work with ordinary steps. The one known limit is
an element that *is itself* an iframe (rich-text editors): `type` against it fails in
WebDriver's clear-then-type sequence **[project run, Maximo RTE]** — skip optional rich-text
bodies rather than fight it.

## Locating elements — `object` + `identifiers`

```yaml
object: html.button
identifiers:                       # alternatives: first Widget that matches wins
  - properties:                    # all properties in one Widget must match (AND)
      - content: Save
    locators:                      # optional spatial/structural anchors
      - inside: { object: html.div, properties: [{ content: 'Phone *' }] }
  - properties:                    # fallback Widget
      - xpath: //button[@id='save']
```

**Alternatives are OR, properties within one Widget are AND** **[sample: scripts/ui/contact-us-ui —
`identifiers: [{properties: [label: Contact Us]}, {properties: [placeholder: Name]}]`;
locators/contact-us-element-locator-ui — `placeholder: [{val: '!Name'}, {includes: address}]`]**.

### `object` catalog

`object` is a free string **[schema]** resolved at runtime; the convention is `html.<tag>` with
`<input>` specialised by `type`. Seen executing in the product corpus **[samples]**:

| Element | `object` |
|---|---|
| `button` / `a` / `img` / `div` / `span` / `p` / `li` / `label` / `i` / `h1..h6` / `body` / `html` | `html.button` … `html.html` |
| `input type=text` / `email` / `password` / `radio` / `checkbox` / `submit` / `button` / `color` | `html.inputtext`, `html.inputemail`, `html.inputpassword`, `html.inputradio`, `html.inputcheckbox`, `html.inputsubmit`, `html.inputbutton`, `html.inputcolor` |
| `textarea` / `select` | `html.textarea` / `html.select` |
| unlabeled input located by xpath/position | `html.inputtextfield` **[CycleStore]** |
| jQuery Mobile / UI widgets | `jquery.jqmbutton`, `jquery.jqmradio`, `jquery.jqmcheckbox`, `jquery.jqmselect`, `jquery.jqmsearchinput`, `jquery.jqmcollapsibleheader`, `jquery.jquitab`, `jquery.jquimenuitem` |
| native dialogs | `window.ok`, `window.cancel`, `window.popup` |

Derive the tag/type from the live DOM (see "Deriving `object`" below); for an unlisted tag use
`html.<lowercase-tag>` and flag it as unconfirmed.

### `properties` catalog and operators

Keys seen in UI samples: `content` (rendered text), `label`, `placeholder`, `src`, `id`, `name`,
`xpath`, `tagname`, `focus`, `exist`, `visible`, `enabled`, `message` (dialogs).

Each property value is either a scalar (shorthand for `val`) or a list of operator items
**[schema: `Field`/`FieldItem`]**:

```yaml
- content: Save                         # scalar == [{val: Save}]
- content: [{ val: Save }]              # structured form (what the recorder emits)
- content: [{ regex: '[1-3]' }]
- content: [{ ends: '(0)' }]            # also starts, includes
- placeholder: [{ val: '!Name' }, { includes: address }]   # leading ! negates; items AND together
- content: [{ regex: '!.*${THING}.*' }]
- content: [{ var: EXPECTED }]          # compare with a variable
- id:      [{ js: 'value => value.startsWith("m")' }]
```

**Scalar shorthand is schema-valid and is what the product corpus uses.** One Test Hub *visual
editor* version observed in this project rejected scalar `id:`/`xpath:` (“items expects an
array”) **[project run]** — so use the structured `[{val: ...}]` form when the assets will be
opened in that editor; it is never wrong, merely verbose.

Quote XPath containing `:` or `[`…`]` **[YAML]**: `xpath: [{ val: "//span[contains(@id,'_tdrow_[C:1]')]" }]`.

### `locators`

Kinds **[schema: `Locator`]**: `above`, `below`, `leftof`, `rightof`, `near`, `inside` (each an
`object` + `properties` + optional nested `locators`), `position`, `js`.

- `position: '1'` is **1-based** **[project run: `'0'` failed, `'1'` passed on the same page]**;
  the samples use `'1'`/`'2'` **[sample: locators/*]**.
- `js: return document.querySelector('input[class="${CLASS}"]')` — a JS locator that returns the
  element directly **[sample: locators/contact-us-element-locator-ui.dtx.yaml]**. The most
  powerful escape hatch when semantic properties fail; keep it rare and note why.
- Nested anchoring works: `rightof` a label that is itself `above` another label **[sample:
  locators/nested-locator.dtx.yaml]**.
- `inside` + `includes` against a large container failed once in a real run even though the
  text was present **[project run]**; the confirmed `inside` precedent is a small wrapper with
  `val`. Prefer `position` on a confirmed-ordered list when picking "the newest item".

## Environments (`.dte.yaml`) and credentials

```yaml
defaultUser: ACTOR1
users:
  ACTOR1:
    username: Alice
    password: { expr: password1, type: secret }   # key into the secrets collection
    token: sometoken
secrets: mySecretCollection
vars:
  APP_URL: https://app.example.test/
  SECRET_FROM_NAME: { type: secret }
profiles:
  chrome+medium.phone: { device: 'pCloudy:pixel' }
  windows: DAWN_LAPTOP                              # profile -> agent
includes:
  - sub/env-child.dte.yaml
```

**[schema: environment.json; samples: environment/*]**. Scripts consume it with
`${user('username')}` / `${user('password')}` (optionally scoped by `with: {user: ACTOR2}`), or
by declaring `NAME: {}` / `NAME: {type: secret}` vars that the environment fills.
**Never write a real password as a literal in a `.dtx.yaml`** — the corpus's earliest design
note already says so, and the mechanism to avoid it is the environment file plus `type: secret`.

## Suites (`.dts.yaml`)

```yaml
note: Smoke pack
configuration:              # [schema: SuiteConfiguration]
  concurrent: '2'           # parallelism ('0' = unbounded); omit for sequential single-profile runs
  sequential: 'true'        # run tests in order even with multiple profiles
  profiles: [chrome, edge, { name: linux, capabilities: [{ os: linux }] }]
  stepTimeout: 10min
  vars: { ABC: xyz }
  dataset: rows.csv         # data-driven suite
tests:
  - Login Smoke.dtx.yaml
  - url: Create Asset.dtx.yaml
    profiles: [chrome]
  - url: tests/*.dtx.yaml           # wildcards: *, **, **/*.dtx.yaml
    excludes: [tests/*skip*, '!tests/*no-skip*']   # ! re-includes
  - url: '${FILE}'                  # driven by a dataset column
    dataset: which-tests.csv
  - other-suite.dts.yaml            # suites nest
```

**[samples: suites/*, scripts/wildcard/*, scripts/concurrent-suites/*]**. Each `tests` entry is a
`RunStep`, so `in`, `dataset`, `inline`, `profiles`, `excludes`, `note` all apply.
Suite `configuration` is schema-valid and used throughout the product corpus; one Test Hub
server/editor version in this project rejected a suite containing it **[project run]** — if the
target server is unverified, start with `note` + `tests` and add configuration once it renders.
List tests, not modules, in a suite.

## Data-driven testing (CSV)

- Header row = variable names. Bind with `type: column` **[sample: data-driven/pull-data.dtx.yaml]**:
  `configuration: {dataset: users.csv, vars: {USERNAME: {expr: USERNAME, type: column}}}`.
- `run: {url, dataset}` or a suite entry with `dataset` runs the target once per row; `iterate`
  loops in place; `assign: {dataset, vars: {X: {type: column}}}` advances a cursor and pulls
  the next row **[sample: data-driven/pull-data.dtx.yaml]**.
- Filters and joins: `dataset: {url: items.csv, where: {USER_ID: {val: '${CUSTOMER}'},
  QUANTITY: {js: 'value => value > 4'}}, additional: [employees.csv]}` **[sample:
  data-driven/where-test.dtx.yaml, datadriven-additional/*]**.
- `.ddf`/`.cgen` generator files (CycleStore) remain valid for synthesised data; the product corpus
  itself is CSV-only.

## Recorder output and legacy forms — what to clean up

The recorder emits **[sample: recorder/test_ua.dtx.yaml]**: `shot: shot/<id>.dti.jpeg#<offset>`
on each step, `meta: {browserName, ...}` on `open`, structured `content: [{val: X}]` properties,
`locators: [{position: 'N'}]` for disambiguation, one `with` per page titled with the page
title, and sometimes placeholder steps (`- log: {}`, `- pause: {}`, `- type: {}`) and YAML
artifacts (`- ? '' :`). Remove placeholders and artifacts; `shot` is optional.

Legacy forms that still appear in old files but are superseded **[sample: legacy/old.* vs
legacy/updated.*]**: `pause: {duration: 1s}` → `wait: 1s`; root-level `vars`/`cache`/
`stepTimeout` → under `configuration:`; suite root `concurrent`/`stepTimeout`/`vars` → under
`configuration:`; `timeout:` is not a field (use `stepTimeout`); `:xpath` keys are not valid.
`applicationName`/`description` in a `.dtc.yaml` are not in `component.json` — an editor
artifact; the schema rejects them.

## Project-observed runtime behaviours (version-specific; re-verify if a run contradicts)

- `position` is 1-based (confirmed by a passing run).
- `inside` + `includes` on a large container failed despite matching text.
- An element `wait` without `stepTimeout` reported `duration is null`.
- Rendered text vs raw DOM text: `content` matches what is *rendered* (CSS `text-transform`
  applied), e.g. `Pending` not `pending`.
- A second `open` to the same window mid-test reloaded an SPA and lost state.
- One visual editor rejected scalar `id:` and any suite `configuration`.
- MAS/Maximo: the classic UI lives in an iframe (transparent to element resolution); side-nav
  `data-testid` anchors of collapsed groups exist in the DOM but are `visibility: hidden`, so a
  click hits a different element; several `data-testid`s are duplicated; apps deep-link via
  `?event=loadapp&value=<app>`; cold app load ~25 s.

## Grounding tests in the real application — mandatory, but do it fast

**Never author a new step by pattern-matching or recombining steps from other tests.** Every
`object`/`properties`/`xpath` value in a new step comes from observing the live target in a
real browser this session, from a smartshot the user chose, or from `LIVE-NOTES.md` facts that
still hold. Reusing an *entire module* via `run:` is encouraged; reusing fragments of unrelated
tests is not.

This skill targets test/staging instances. Interact freely; pause only if the URL looks like
production.

Before writing any new step:

1. **Get the target URL** from `.dtc.yaml` or the user. 2. **Get the scope.** 3. **Read
`LIVE-NOTES.md`** for the component and trust what it covers. 4. **Drive the flow efficiently**
(below). 5. **Capture each element's real `object` and properties from the live DOM** before
writing its step. 6. **Translate into `with:` blocks** in the order it happened. 7. If an existing
module no longer matches the live app, **say so** — don't silently edit it to a guess. 8.
**Update `LIVE-NOTES.md`.**

This session's browser is a different engine from Test Hub's runner; a grounded test still
needs one real Test Hub run.

### Efficient browser driving

- Prefer one JS-execution call per logical interaction (fill+submit a form; open a menu and read
  its structure) over one call per click. Return compact text summaries, not screenshots.
- Verify with text (`location.href`, `document.title`, a targeted `innerText`), not vision.
- **Interactability test**: `document.elementFromPoint(cx, cy)` at an element's centre tells you
  what a real click would hit. An element with a non-zero rect but `visibility: hidden` (or a
  clipped ancestor) is "found" by a locator and *not* clickable **[live DOM, Maximo side-nav]**.
- **Frames**: when a probe finds no matching controls, check `document.querySelectorAll('iframe')`
  and probe `frame.contentDocument` — the app may live inside one.
- **Duplicate identifiers**: count matches (`querySelectorAll(...).length`) for any `id`/`data-*`
  you intend to use; duplicates need a `position` or a stronger anchor.
- Pitfalls: coordinate clicks need a same-scale screenshot and mis-hit under OS scaling; ref-based
  clicks go stale after navigation; JS `el.click()` bypasses visibility checks, so it is fine for
  *reaching* a page during discovery but proves nothing about whether Test Hub can click it.

### Reusing confirmed facts — `LIVE-NOTES.md`

Keep `<Component>/LIVE-NOTES.md` as a factual cache: confirmed `object` mappings, label
conventions, text-case quirks, routes/deep links, load times, banner behaviour, app quirks, and
which modules still match. Check it before any live work; add to it after. Invalidate when the
user says the app changed, a Test Hub run contradicts it, or you observe otherwise.

### Deriving `object` and identifiers from the live DOM

```js
(() => {
  const el = document.querySelector('<something you just interacted with>');
  if (!el) return null;
  const cs = getComputedStyle(el), r = el.getBoundingClientRect();
  return {
    tag: el.tagName.toLowerCase(), type: el.type || null,
    text: el.innerText?.trim(), label: el.labels?.[0]?.innerText?.trim(),
    placeholder: el.placeholder || null, id: el.id || null, src: el.src || null,
    visible: r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none',
    hit: document.elementFromPoint(r.x + r.width/2, r.y + r.height/2) === el,
    inFrame: window !== window.top,
  };
})()
```

Map `tag`/`type` to `object` with the catalog above; prefer `label`/`content`/`placeholder`
over `id`, `id` over `xpath`, and read `xpath` from the real DOM when you must.

## Writing a new browser test — checklist

1. URL and scope known; component located or created (`.dtc.yaml`).
2. Existing modules inspected; reuse decided once.
3. `LIVE-NOTES.md` read; only the gaps driven live.
4. Every seam between composed pieces confirmed live; bridged with a real in-app `click` (or a
   verified deep link / named-context `open` — never a same-window reload of an SPA).
5. Steps grouped in `with:` blocks; semantic properties preferred; `shot` omitted.
6. Anything that may be absent wrapped in an element-form `if`; anything load-dependent guarded
   by an element `verify`/`wait` with an explicit `stepTimeout`.
7. URLs, credentials, seeds as `vars`; credentials via `type: secret`/environment, never literal.
8. Every referenced `${Var}` declared locally; modules composable (no `open`, own var
   declarations).
9. Validated: real YAML parse, one action key per step, schema (`additionalProperties: false`),
   `run:`/suite paths resolve, `git diff --check`.
10. Committed/pushed to the agreed branch; run once in Test Hub; `LIVE-NOTES.md` updated.
