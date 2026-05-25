# service-clients/idp-client/

Python client (library + Typer CLI) for the ocr-svc IDP REST API. Wraps the api-lib HTTP surface; never imports from `api_lib` (clients are wire-protocol consumers).

## Layout

- `openapi/openapi.json` — committed OpenAPI snapshot. Hand-authored today (api-lib's extraction routes haven't fully landed). Once api-lib stabilizes, run `make regen-spec` to pull a live `/openapi.json` and overwrite this file.
- `src/idp_client/_generated/` — `openapi-python-client` output. Checked in. Do NOT hand-edit. Excluded from ruff/mypy/coverage. Regenerate via `make regen`.
  - Models are **attrs**, not Pydantic v2. openapi-python-client 0.28 dropped the `use_pydantic_v2` config flag; the generator's only mode is attrs. Facade calls `Model.from_dict(...)` / `instance.to_dict()` at the boundary. Public re-exports stay attrs-typed; this is consistent and removes a runtime dep.
- `src/idp_client/client.py` — sync `IdpClient` facade.
- `src/idp_client/async_client.py` — async `AsyncIdpClient` facade (Phase 3).
- `src/idp_client/auth.py` — env / param API-key resolution.
- `src/idp_client/errors.py` — exception hierarchy + `application/problem+json` mapping.
- `src/idp_client/compat.py` — opt-in lazy server-version compat check (see `compat_check=`).
- `src/idp_client/cli.py` — Typer app, registered as the `idp-client` console script.
- `tests/unit/` — `respx`-mocked, fast, default. Marker: `unit`.
- `tests/live/` — opt-in smoke against `IDP_BASE_URL` (Phase 3). Marker: `live`.

## Wire conventions

- **Auth header:** `X-Api-Key: <token>` (Q2:B). `auth.py` resolves explicit param, then `IDP_API_KEY` env, then raises `IdpAuthError`. Customer logging stacks should add `X-Api-Key` to their redaction rules — unlike `Authorization`, it is not redacted by default.
- **Telemetry headers:** `User-Agent: idp-client-py/<version>`, `X-Idp-Client: py/<version>` on every request.
- **Error envelope:** RFC 7807 `application/problem+json`. Mapped to typed exceptions in `errors.py`.
- **Versioning:** `__version__` is the client semver; `__api_lib_version__` is parsed from `openapi/openapi.json` at import. Surface used by `compat_check`.

## Generator workflow

```
api-lib /openapi.json    ──[ make regen-spec ]──►  openapi/openapi.json
openapi/openapi.json     ──[ make regen ]──►       src/idp_client/_generated/
```

CI gates against drift: `make regen && git diff --exit-code src/idp_client/_generated/` must produce no output. Update both the snapshot and the generated tree in the same PR.

The OpenAPI snapshot declares an `ApiKey` security scheme with `in: header, name: X-Api-Key`. This trains the generated `AuthenticatedClient` to inject the right header without facade plumbing. Verify after every `make regen` — if the generator stops honoring this, fall back to an unauthenticated `Client` and inject `X-Api-Key` from the facade per request.

## Testing

- Default: `make test` runs `pytest -m unit` (respx-mocked, no network).
- Coverage target ≥85% on hand-written code. `_generated/` is omitted.
- Phase 3 introduces `make test-live` (`pytest -m live`). Skipped when `IDP_BASE_URL` is unset.
- Multipart upload is exercised via `respx` body matchers — there is no in-memory ASGI fixture for upload routes.

## What lives elsewhere

- The api-lib REST contract is owned by `api-lib/`. This package never imports `api_lib`.
- Customer documentation tier is deferred. See `README.md` for usage; cross-link from `docs/docs/developer-docs/api/` lands in Phase 3.
- TS / Go / Rust clients each get their own `service-clients/idp-client-{lang}/` sibling package and generator pipeline. Out of scope here.
