# DevOps Test Hub skills for Claude Code

Teach [Claude Code](https://claude.com/claude-code) to write tests for **HCL DevOps Test Hub**.

Test Hub stores tests as plain YAML files in a git repository (`.dtx.yaml` tests, `.dts.yaml` suites, `.dtc.yaml`
components). With these skills installed you describe the test you want in plain English, and Claude checks the real
application or API, writes the YAML in the right format, validates it, and puts it in your test repository ready to run.

## What you can do with it

| You want to… | Example thing to say to Claude | Skill |
|---|---|---|
| Create **API tests** (REST/JSON over HTTP), from an OpenAPI/Swagger file or by exploring a live service | "Write API tests for the orders service at http://localhost:5000/api. Start with simple GET tests, then login flows, then a test that orders two items and checks the total." | `devops-test-browser` |
| Create **browser/UI tests** by driving the real web app | "Create a Test Hub browser test that registers a user on https://shop.example.test and checks the welcome page." | `devops-test-browser` |
| Extend or explain existing tests | "Why does this test fail?" (paste a Test Hub result or link) · "Add a suite that runs the checkout tests." | `devops-test-browser` |
| Migrate IBM **Maximo** UI tests (Selenium/TestNG/`.bin` recorder files) to Test Hub | "Convert the Maximo work-order smoke tests in this folder to Test Hub tests." | `maximo-testhub-migration` |

You don't invoke anything special: Claude loads the right skill when your request matches it.

## Why API tests need this

In the Test Hub 12.0 tech preview the only built-in way to create an API test is to **record** browser traffic against an
imported schema; there is no palette for building one by hand. These skills fill the gap by writing the YAML directly. Test Hub
opens hand-written API tests normally and shows them as `Send <url>` → `Send Request` / `Receive Response` → one node per check.

Here is the smallest working example (this exact shape passes in Test Hub; only the URL differs):

```yaml
note: GET the health endpoint
steps:
  - send:
      url: http://localhost:5000/api/health
      request:
        fields:
          - method:
              - val: GET
      response:
        fields:
          - status-code:
              - val: '200'
          - content/status:
              - val: ok
```

## Before you start

You need:

1. **Claude Code** (the CLI, the desktop app or the VS Code extension).
2. A **Test Hub project with a git-backed test repository** that you can push to. Claude writes files into a clone of that repo.
3. A **test or demo environment** to test against — a web app URL for browser tests, a base URL for API tests. Don't point these at
   production: Claude will interact with the target (register users, place orders, click buttons) the way a tester would.
4. Optional but helpful: Python 3 on your machine (Claude uses it to validate generated files against the JSON Schemas; it can install
   the one package it needs), and Test Hub's own MCP server if you have it connected (lets Claude read project and result data).

## Install

Clone the repo, then make each skill folder visible to Claude Code under `~/.claude/skills/`
(Windows: `%USERPROFILE%\.claude\skills\`). Claude Code picks the skills up the next time you start a session.

```bash
git clone https://github.com/virtualmonster/DevOpsTestHub-Skills.git
```

**Option A — link it (recommended, so `git pull` updates the skills):**

```powershell
# Windows (PowerShell)
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills" | Out-Null
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\devops-test-browser" -Target "$PWD\DevOpsTestHub-Skills\skills\devops-test-browser"
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\maximo-testhub-migration" -Target "$PWD\DevOpsTestHub-Skills\skills\maximo-testhub-migration"
```

```bash
# macOS / Linux
mkdir -p ~/.claude/skills
ln -s "$PWD/DevOpsTestHub-Skills/skills/devops-test-browser" ~/.claude/skills/
ln -s "$PWD/DevOpsTestHub-Skills/skills/maximo-testhub-migration" ~/.claude/skills/
```

**Option B — copy it:** copy the folders under `skills/` into `~/.claude/skills/`. Re-copy after each `git pull`.

Prefer to keep a skill with one project only? Put the folder in that project's `.claude/skills/` instead.

**Check it worked:** start a new Claude Code session and ask, *"What can the devops-test-browser skill do?"* — it should describe
browser and API test generation. If you only need one of the two skills, install just that folder.

## Your first tests

### API tests

1. Open Claude Code in a **clone of your Test Hub test repository**.
2. Ask for what you want, for example:
   > Create API tests for the SendIt Cycles API at http://localhost:5000/api. The OpenAPI file is in `schemas/`. Start with atomic GET tests,
   > then register/login tests, then a workflow that orders 2 of a product and checks the price and total are correct.
3. Claude will ask only what it can't work out: the target base URL, which branch to push to, and whether state-changing calls are OK
   on that host. It then probes the service, writes the tests, validates them, and (if you ask) commits and pushes.
4. In Test Hub, run the suites in this order: **Atomic → Auth → Workflow**. Bring any failure back to Claude (the step and message) and it
   will diagnose from the real response and fix one thing at a time.

What you get, in a folder per tier (see `skills/devops-test-browser/examples/SendItCycles-API/` for a full example):

| Tier | What it contains |
|---|---|
| Atomic | One call, one idea: `GET Health`, `GET Product By Id`, `GET Product Not Found` — read-only wherever possible |
| Auth | Register, login (valid / wrong password / unknown user), profile with and without a token, 401 vs 403 access control |
| Workflows | Chained calls that assert *relationships*: price × quantity = order total, stock falls by the quantity ordered, list view = detail view, one user can't see another's order |
| Known Issues | Tests asserting the **correct** behaviour of defects found while exploring, so they fail until fixed and then guard the fix |
| Shared module | `Register And Login` — creates a throwaway user and returns the token to any test that needs one |
| Suites | One per tier plus an "All" suite (which leaves out Known Issues) |

### Browser tests

1. Open Claude Code in your test repository clone.
2. Tell it the app URL and the flow. Claude searches for existing recordings ("smartshots") and modules, and offers to generate from
   them, drive the live app, or mix both.
3. It walks the real app, captures how each element can be identified, writes the test (reusing existing modules where it can), validates
   it, and pushes to the branch you chose.
4. Run it in Test Hub and bring back any failure.

## How it keeps tests honest

- **Grounded, not guessed.** Every selector, status code, error message and field name comes from the live app/service, the OpenAPI/source,
  or an existing proven module — not from pattern-matching other tests.
- **Checked before publishing.** Each file is validated against Test Hub's JSON Schemas (a misspelt field is rejected outright by Test Hub),
  paths and suite entries are checked, and for API tests every assertion is replicated with an independent client first.
- **Safe defaults.** Throwaway test data with per-run generated values and passwords; no literal credentials or tokens in generated files;
  it will not forge tokens, guess passwords or bypass auth (privileged calls need a token you supply through a Test Hub environment secret);
  it avoids inputs that could corrupt a shared host (negative or zero quantities, oversized payloads); each suite's side effects are listed
  in the component README it writes.
- **Verified in Test Hub.** Claude can't run Test Hub's engine itself, so the loop is: it generates, you run, it reads the real failure and fixes.
  If Test Hub's MCP server is connected it can also read results directly.

## What is confirmed, and what isn't

The worked API example (`SendItCycles-API`) was run in Test Hub: **all 26 tests in its Atomic, Auth and Workflow suites pass.** That
confirms plain `send` steps, `${VAR}` URLs, value capture, `verify` expressions, POST bodies, expected 4xx responses with error text,
whole-body capture with a JSON-parsing helper, bearer-token auth, passing values out of a module, array captures, and the
stock/total/isolation assertions.

Not yet run in Test Hub: the example's Known Issues suite, and **schema-driven sends** (`schema: file.yaml#operationId`).
The construct table in [`reference/api-guide.md`](skills/devops-test-browser/reference/api-guide.md) lists each construct as confirmed or
only authored, and is updated from every Test Hub result.

Out of scope: SQL, stubs (`.dtv`), gRPC and load profiles. Tested against the Test Hub 12.0 tech preview; the skills handle both the
`2026/05` and `2026/07` DSL schema versions (they write the form that works on both).

## Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| A test opens in the code view but the visual view says "parsing error" | A schema violation, not bad YAML. Hover the red squiggle: the message names the expected type. Older servers need list-form values (`- val: x`), which the skill writes. |
| A module returned nothing to the calling test (`TOKEN` is empty, API says "No token provided") | `run: out:` maps *module var → caller var* and the caller name must be spelled out: `TOKEN: [TOKEN]`. An empty `TOKEN: {}` validates but maps nothing. |
| `curl -i ...` in PowerShell asks for `Uri:` | In Windows PowerShell 5.1 `curl` is an alias for `Invoke-WebRequest`. Use `curl.exe`. |
| Test Hub API recording says "no interactions found" | Unconfirmed causes: spec `servers` host/port differs from the traffic's, the base path (`/api`) is split between `servers` and `paths`, or operations lack `operationId`. The skill's OpenAPI files include `operationId`s. |
| A port returns `404 page not found` for everything | It may not be your service (for example a Docker registry on :5000). Check the `Server` and other response headers. |

## Repository layout

```
skills/
  devops-test-browser/          browser/UI + API test generation
    SKILL.md                    entry point Claude reads: routing, workflows, permission policy, validation gates
    reference/
      dsl-guide.md              file types, variables, step catalog, modules, suites, data-driven tests, schema versions
      api-guide.md              the `send` step, captures, auth and chaining, suite design, live-grounding procedure,
                                confirmed-vs-authored construct table
      testhub-mcp-tools.md      using Test Hub's MCP server to review results (optional)
      schemas/                  Test Hub JSON Schemas (2026/07)
      samples/                  curated browser-test precedent from the product's own sample corpus
    examples/
      CycleStore/               browser component example, with LIVE-NOTES.md
      SendItCycles-API/         API component example: 30 tests, login module, 5 suites, OpenAPI 3 file with operationIds,
                                generator script, LIVE-NOTES.md (hosts sanitised to localhost)
  maximo-testhub-migration/     Maximo Test Automation Framework (MAS 9.1) UI tests → Test Hub, with live-confirmed MAS facts
                                (deep-link app loading, iframe layout, consent banners, navigation pitfalls)
```

`LIVE-NOTES.md` files are caches of facts confirmed against a real app or service. Claude reads one before testing that target and adds
to it when it confirms something new.

## Contributing

- Found a construct that works or fails in Test Hub? Update the status table in `reference/api-guide.md` (or the relevant section of
  `reference/dsl-guide.md`) with the result and the exact fix.
- Added or changed a component example? Keep it free of real credentials, tokens and internal hostnames — use `localhost` or placeholders.
- Keep generated example files valid: they should pass the JSON Schemas in `reference/schemas/`.
