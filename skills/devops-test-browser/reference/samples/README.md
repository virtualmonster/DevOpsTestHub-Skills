# Product-authored DSL samples (curated)

Copied from the vendor's own `onetest-server` `lang/samples` corpus (mirrored in the
`onetest-ideas-dsl` repository, schema version `2026/07`). These are the runtime's unit tests:
a construct that appears here is known to execute. They are **precedent**, not templates —
never copy selectors from them into a real test.

Many reference a local stub (`run: *.dtv.yaml`, `${stub('http://...')}`); ignore that plumbing
and read the browser steps.

| Folder | What it proves |
|---|---|
| `frames/` | Inputs three framesets deep are typed into with plain `object` + `label` — **no frame-switching step exists or is needed**. Also: `open` as the third step, inside a `with`. |
| `flow/` | `if` with an **element** as the condition (+ `stepTimeout` to bound the probe), `while`/`do` element-conditional loops, `assign` reading `content` into a var, `wait` **for an element** with `stepTimeout`. |
| `controls/` | Every HTML control kind (`html.inputradio/checkbox/submit/button/color`, `html.textarea`, `html.select`), `use: right_click/double_click/hover/drag` + `to`, `press: enter`, `verify` with `enabled`/`visible`/`ends`/`xpath`, `assign` + `exist` → `if condition`, `verify exist: 'false'`, native dialogs via `window.ok/cancel/popup`, multi-line values, jQuery widget objects. |
| `locators/` | `above/below/leftof/rightof` anchors, nested locators, `position: '1'/'2'`, the `js:` locator returning an element, `!` negation and `includes` on properties, alternative `identifiers` entries. |
| `tabs-windows/` | `open` with `attach: 'true'` + `context: name` for app-opened tabs, `with: context:`, `run: context:`, four `open`s in one test, named contexts, device-emulation profile `edge+medium.phone`. |
| `modules-vars/` | `in`/`out`/`local` modifiers, `{}` (declared, no default) vars, failure propagation from module to caller, scoped variable inheritance, `type: js` numbers/booleans, **functions as variables** (reusable JS helper modules), `relative: 'true'` paths, `while`/`if`/`wait`/`assign` flow. |
| `data-driven/` | CSV datasets, `type: column` binding, cursor `assign dataset`, `iterate`, `where` filters (`val`/`js`), column remapping via `run: in:`. |
| `suites/` | Suite `configuration` (`concurrent`, `sequential`, `profiles`, `vars`), per-test `profiles`, wildcards (`*`, `**`), `excludes` with `!` re-include, nested suites. |
| `environment/` | `.dte.yaml`: `users` with `type: secret` passwords, `defaultUser`, `secrets`, `vars`, `includes`, `profiles` → agents/devices; consumption via `${user('username')}` and `with: user:`. |
| `legacy/` | Old vs updated file shapes: `pause` → `wait`, root-level `vars`/`cache`/`stepTimeout`/`concurrent` → under `configuration`. |
| `recorder/` | What the recorder emits (`shot`, `meta`, structured `[{val}]` properties, `position` locators, placeholder steps to delete), plus the product's own login idiom (`verify focus` → shorthand `type` → `press`). |

The full corpus also covers API (`send`), SQL, stubs, messages, transports, gRPC, load
profiles and browser-driven API recording; those are out of scope for this skill.
