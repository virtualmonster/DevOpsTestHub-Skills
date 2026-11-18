# SendItCycles-API — worked API test component

A complete API test component for the SendIt Cycles demo store (Express backend, SQLite), kept as the
**reference example for API tests**, the way `../CycleStore/` is for browser tests. It is an illustration of layout,
naming and step shapes — not a target to assume; always ground a new component against the service the user names.

| Path | What it shows |
|---|---|
| `.dtc.yaml` | Component definition (`type: web`) |
| `1 Atomic/` | One-call read-only checks, incl. 404 and image tests |
| `2 Auth/` | Register, login (valid/invalid), profile, token errors, 401/403 access control |
| `3 Workflows/` | Chained flows: price × quantity = total, stock delta, list = detail, user isolation, validation |
| `Known Issues/` | Tests asserting the correct behaviour of confirmed defects (they fail until fixed) |
| `modules/Register And Login.dtx.yaml` | Shared setup module with `out` vars (token, user id, generated credentials) |
| `_* Suite.dts.yaml` | One suite per tier plus `_All API Tests Suite` (excludes Known Issues) |
| `schemas/senditcycles-openapi.yaml` | OpenAPI 3 derived from source and verified live; `operationId` on every operation |
| `_generator/gen_api_tests.py` | The script that emitted every test above in one consistent shape (pass output root and base URL) |
| `LIVE-NOTES.md` | Confirmed API facts, defects and Test Hub results — read before testing this service |

`BASE_URL` is `http://localhost:5000/api` (placeholder); each test declares it as a var so a suite or environment can
override it. Regenerate with `python _generator/gen_api_tests.py <output-root> <base-url>`.

Status: authored from live-verified API behaviour. In Test Hub the plain `GET Health` test passes and renders;
many of the others pass and some do not — see `LIVE-NOTES.md` and the construct table in `reference/api-guide.md`
for what has and has not been confirmed.
