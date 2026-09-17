# Test Hub MCP tools — closing the verification loop

Everywhere else in this skill, "browser-grounded doesn't mean guaranteed to pass" — this skill's
own live-browser walkthrough uses a different engine than Test Hub's actual runner, so a
generated test could still fail for reasons this skill can't see (exactly what happened with the
first version of the CycleStore order-lifecycle test: it looked right, and still failed a real
Test Hub run over a composition issue that hadn't been actually executed end-to-end).

**If Test Hub's own MCP server is connected this session** (tools named `testhub__*` — check with
a quick tool search if you're not sure), use it for discovery and result review, and use execution
when securely authenticated. The execution endpoint requires an `offlineToken` generated from the
Test Hub UI, while the MCP server itself must separately authenticate project, test, and result
queries. Never ask the user to paste a token into chat. If read-only tools such as `get_projects`
also return `401 Unauthorized`, retry the same read-only call once; if it still fails, treat that
as a server/MCP authentication outage rather than an execution-token problem.

## What's documented (source: HCL DevOps Test Hub MCP server spec, v11.0.9)

This is sourced from product documentation, not from having actually called a connected server —
**confirm the real parameter names/shapes against the connected tool's own schema** (they're
fully typed once loaded) before relying on the details below, in case a version differs from what
was documented.

| Tool | Parameters | Purpose |
|---|---|---|
| `testhub__get_projects` | *(none)* | List projects and any project metadata exposed by the server, including a repository/SCM URL when available; use it to find the `projectId`. |
| `testhub__list_tests` | `projectId`, `branch` | List the tests Test Hub sees for a project on a given branch. Use this to find the `assetId` of a test you just committed/pushed — match by name/path. |
| `testhub__run_test` | `projectId`, `assetId`, `branch`, `offlineToken` | Execute a test (or suite) in Test Hub. The offline token is generated from the Test Hub UI. Returns an execution/run id. |
| `testhub__get_result_by_id` | `projectId`, `resultId` | Fetch the detailed result (pass/fail, step-level detail) for one run. |
| `testhub__get_results` | `projectId`, `branch` | List result summaries across recent runs for a project/branch. |

Use a repository/SCM URL returned by `testhub__get_projects` when one is present. If the response
does not expose one, inspect the current checkout's git remote. Ask the user for the repository
URL only when neither TestHub metadata nor the local checkout provides it. Project metadata is
not a component registry: identify components from `.dtc.yaml` files in the checkout.

## Workflow: verify a generated test for real

1. Finish generating the test as usual (browser-grounded, schema-checked) and **commit and push it
   to the branch Test Hub is tracking** — Test Hub cannot see local uncommitted files.
2. `testhub__get_projects` -> resolve the `projectId` once, including team space when names repeat;
   reuse it for the rest of the session.
3. `testhub__list_tests` with `projectId` and `branch`, using a name filter when available -> find
   the exact `assetId` by path/name. Do not assume a same-named asset is the new one.
4. Choose the verification mode:
   - **Review mode**: use `testhub__get_results` with the known project/branch and asset filter,
     then `testhub__get_result_by_id` for the selected run. Prefer the result whose asset, branch,
     version/commit, and start time match the change.
   - **Execution mode**: call `testhub__run_test` only when a secure offline token is already
     available. Never fabricate or request the token in chat. The tool may return a run ID; fetch
     its detail with `testhub__get_result_by_id`.
5. Poll an asynchronous result with bounded backoff (at least 60 seconds before the first check,
   then 30, 45, 60, and 90 seconds) only while it remains `RUNNING`. Do not poll a completed result
   or query every project result repeatedly.
6. **Report the actual result** — pass, fail with the step and evidence, still running, not run, or
   blocked by authentication. An authentication block is not a test failure.

For a suite, review the suite result first, then inspect child results only when the suite fails or
the user asks for per-test detail. For several independent tests, filter results by each exact asset
ID rather than relying on the global newest-results order.

## Fix-and-rerun loop

When a run fails, don't just report it and stop — close the loop yourself if the failure looks
fixable from the evidence:

1. **Read the actual step-level failure detail** from `get_result_by_id` (which step, what error —
   "Object not found", a timeout, an assertion mismatch) before touching anything. Don't
   pattern-match to a past failure in this project unless the evidence genuinely matches.
2. **Decide if the fix needs new live-browser grounding.** A locator that no longer matches (the
   app changed, or the original selector was wrong) needs a real re-check of the live DOM — go
   back to the actual app, confirm what's there now, and derive the corrected `object`/`identifiers`
   from that, exactly as in initial generation. Never hand-edit a selector to "probably" fix a
   failure without re-observing the real page — that's the same fabrication risk this skill avoids
   everywhere else.
3. **Make one grounded fix at a time**, update the `.dtx.yaml`, commit and push it, then execute or
   review the exact asset again and fetch the new result. Don't batch up multiple speculative fixes
   before re-running — each run either confirms or rules out exactly one change.
4. **Bound the loop to 3 attempts.** If it's still failing after 3 grounded fix-and-rerun cycles,
   stop and report to the user: what's been tried, what each attempt's real result showed, and
   what remains unexplained — rather than continuing to iterate blindly. A repeated failure after
   several grounded attempts is itself a signal (a real app bug, a Test Hub/DSL behavior this
   skill doesn't have precedent for, or a flaky environment) worth surfacing rather than masking.
5. **Every re-run must be a real Test Hub run**, not just this session's own live-browser
   walkthrough re-confirming the same DOM fact — the point of this loop is catching what the
   walkthrough engine can't see (composition issues, Test Hub-specific element resolution
   behavior), so skipping the actual re-run defeats it.

## When these tools aren't available

Not every session will have this server connected. When it's not there, fall back to the existing
guidance: tell the user the test needs a real run in Test Hub, since this skill's own
live-browser verification is a different engine and can't substitute for it.

## Setting this up — likely a dead end in an org-managed desktop app, and why

In the Claude **desktop app**'s Code tab (as opposed to the standalone `claude` CLI in a
terminal), this is **not** configured via `claude mcp add`, `/mcp add`, or a project-level
`.mcp.json` file — none of those apply here:

- The `claude` CLI binary isn't on PATH inside the desktop app's Code tab, so `claude mcp add`
  can't be run from its Bash tool at all.
- `/mcp` in the desktop app's Code tab opens Anthropic's **connector Directory** (the same
  picker used for Slack/Notion/etc.-style connectors), not a config-file-driven server list — a
  `.mcp.json` dropped in the project root is simply not read by this surface.
- MCP servers here are added as **custom connectors** via **Customize → Connectors**. Every
  custom connector already in that list (in the one org this was tried in) only offered
  **Connect**, never **Add new** — registering a brand-new one needs an org/workspace admin;
  regular members can only connect to ones already registered.
- **Confirmed org policy (one real org, found via internal search, not guessed): custom MCP
  connectors are blocked outright** — only vendor-provided ones already on an approved list are
  allowed, for security/maintenance reasons. New tool requests go through the org's IT-request
  process, not a self-serve add.
- **Even past that policy, there's a structural mismatch specific to Test Hub**: the
  custom-connector model is one shared URL for the whole org (fine for one company Slack/Jira),
  but DevOps Test Hub is typically **self-hosted per team/user**, not one shared SaaS instance —
  so a single org-wide connector entry doesn't fit even if policy allowed custom ones. This isn't
  a per-org quirk to work around; treat "this probably can't be connected in a managed desktop
  app deployment" as the default expectation for Test Hub's MCP server specifically, not a
  temporary setup gap.

**Practical implication: don't lead with this integration or block test generation on it.** Check
once (quick tool search for `testhub__*`) at the start of a session and use it if it's there, but
expect it usually won't be, and treat the manual loop below as the normal path, not a fallback.

## The manual loop actually works — lean into it

Across real use, this back-and-forth found and fixed three genuine bugs a live-browser
walkthrough alone couldn't have caught (a mid-test `open:` that broke session state, a nested
`inside`+`includes` locator that didn't resolve against a real container despite the value being
correct, and `position`'s index base) — all without the MCP tools ever being connected. When the
user shares a Test Hub report (screenshot or description):

- Read the actual failure detail (reason, which step, screenshot of page state at failure) before
  proposing a fix — don't assume the cause matches your last guess.
- State concretely what the evidence rules in or out (as opposed to "should work now") before
  proposing the next attempt, and be upfront when an attempt is still a guess rather than
  confirmed — this project's history has both (a wrong-then-right sequence on locator strategy,
  and a since-confirmed fact about index base) precisely because that distinction was kept clear
  each time.
- When something has no precedent anywhere in the schemas or bundled examples (like alert/dialog
  handling — grepped for `alert`/`prompt`/`dialog`/`handler`/`unhandled` across every schema,
  found nothing), say so plainly and point the user at Test Hub's own docs/support rather than
  guessing a third or fourth time at unverifiable syntax.

## Forensics without the MCP server — the report and the REST API

When the user shares a Functional Report (PDF), or is logged into Test Hub in the same Chrome
profile as the browser tool, everything needed to diagnose a failure is reachable read-only:

- **Check the `Git` line first** (`<repository> / <branch> / <commit>`). A project can have several
  repositories connected, and same-named assets in two repositories are ambiguous — a run can
  silently execute a stale copy. Confirm the commit exists in the repository you pushed to before
  diagnosing anything else. `GET /test/rest/projects/{id}/repositories/` and
  `GET /test/rest/projects/{id}/branches/` (trailing slashes required) list what the project tracks
  and the indexed commit per repository. The vendor OpenAPI specs are in the DSL corpus
  (`TestHub-APIOnly/schemas/openapi-testassets.yaml`).
- **Read the failed step's metadata, not just its verdict.** Each step in the report links a
  `Metadata` URL (`/test/rest/projects/{id}/data/buckets/{bucket}/items/{item}/content`). It is
  Test Hub's own element-proxy dump of the page at that moment: a tree of nodes with `tagname`,
  `id`, `content`, and the decisive flags `exist`, `visible`, `reachable`, `enabled`, plus
  `proxyName`/`proxyClass`. "Object not found" with `exist: true, visible: false, reachable: false`
  means the element was there but hidden — fix the interaction order, not the locator.
- **`proxyName` is the `object` vocabulary.** `inputtext`, `inputimage`, `table`, `iframe`
  (`HtmlFrameProxy`) … map directly to `html.<proxyName>`. Read it off the dump instead of guessing
  from the tag.
- Extract PDF text with PyMuPDF when the Read tool cannot rasterise (`fitz`), and print with
  `PYTHONIOENCODING=utf-8` — the reports contain icon glyphs that break cp1252 consoles.
