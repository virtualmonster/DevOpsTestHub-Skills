# DevOps Test Hub skills

Claude Code skills for authoring and migrating HCL DevOps Test Hub tests: browser/UI and API (REST/OpenAPI).

| Skill | Purpose |
|---|---|
| `skills/devops-test-browser` | Generate browser/UI **and API** test assets (`.dtx.yaml`, `.dts.yaml`, `.dtc.yaml`, data files) in the Test Hub DSL, grounded against the live application or service. Includes the DSL guide, an API (`send`) guide, JSON schemas (2026/07), 56 curated browser samples as precedent, and two worked components: `CycleStore` (browser) and `SendItCycles-API` (API). |
| `skills/maximo-testhub-migration` | Migrate IBM Maximo Test Automation Framework (MAS 9.1) browser tests into the Test Hub DSL, with live-confirmed MAS facts (deep-link app loading, iframe layout, consent banner behaviour, navigator pitfalls). |

## Install

Copy (or junction) each folder under `skills/` into `~/.claude/skills/` (Windows:
`%USERPROFILE%\.claude\skills\`). Claude Code picks them up on the next session.

## Layout

```
skills/<name>/SKILL.md            entry point read by Claude
skills/<name>/reference/          DSL guide, schemas, curated samples
skills/<name>/examples/           worked components (devops-test-browser only: CycleStore = browser, SendItCycles-API = API)
```
