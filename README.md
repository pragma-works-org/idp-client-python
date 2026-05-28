# idp-client

Python client (library + CLI) for the ocr-svc IDP REST API.

> Status: **library + CLI complete** (sync `IdpClient`, async `AsyncIdpClient`, `idp-client` Typer CLI). `_generated/` and `openapi/openapi.json` are committed; CI gates against drift. See [`docs/docs/working/specs/svc-idp-client-python/`](../../docs/docs/working/specs/svc-idp-client-python/) for the full spec.

## Install

```bash
pip install -e service-clients/idp-client
# or
uv pip install -e service-clients/idp-client
```

## Auth

The client sends `Authorization: Bearer <token>` on every request. Resolution order:

1. `api_key=` constructor parameter (or `--api-key` CLI flag)
2. `IDP_API_KEY` environment variable
3. Otherwise: `IdpAuthError`

## Library — sync

```python
from idp_client import IdpClient

with IdpClient(base_url="http://localhost:8000") as client:
    health = client.health()
    print(health.status, health.version)

    # Synchronous extraction (small documents).
    result = client.extract("invoice.pdf", format="markdown")
    for page in result.pages:
        print(page)

    # Asynchronous job submission.
    job = client.submit_job("contract.pdf", format="json")
    print(job.id, job.status)
```

Constructor:

```python
IdpClient(
    *,
    api_key: str | None = None,
    base_url: str = "http://localhost:8000",
    http_client: httpx.Client | None = None,    # injected for tests
    timeout: float = 30.0,
    compat_check: bool | str = False,           # True ≡ "minor"; "exact"/"minor"/"major"
)
```

`compat_check` is opt-in. When enabled, the first request lazily probes `GET /health/` and compares `version` against the snapshot bundled with the client (`__api_lib_version__`). Mismatch raises `IdpVersionMismatchError`.

## Library — async

`AsyncIdpClient` mirrors the sync facade method-for-method. Use as an async context manager.

```python
import asyncio
from idp_client import AsyncIdpClient

async def main() -> None:
    async with AsyncIdpClient(base_url="http://localhost:8000") as client:
        health = await client.health()
        print(health.status)

        result = await client.extract("invoice.pdf", format="markdown")
        for page in result.pages:
            print(page)

asyncio.run(main())
```

`_ensure_compat` is `async def` on the async facade and is awaited from every public method. The compat check itself is idempotent — only the first request triggers the probe.

## CLI

```bash
idp-client --help
idp-client health
idp-client version
idp-client extract invoice.pdf --format markdown --languages en,es
idp-client jobs submit contract.pdf --format json
idp-client jobs status job-XYZ
idp-client jobs result job-XYZ --out result.txt
idp-client jobs cancel job-XYZ
```

Global flags (declared on the root command, **must precede the subcommand**): `--api-key`, `--base-url`, `--timeout`, `--output {table|json|raw}`.

```bash
idp-client --output json jobs status job-XYZ
```

## Errors

```
IdpError
├── IdpHTTPError          # status, problem
│   ├── IdpAuthError      # 401 / 403 / missing key
│   ├── IdpNotFoundError  # 404
│   ├── IdpValidationError# 422
│   └── IdpServerError    # 5xx
├── IdpJobFailed          # caller-raised on terminal `failed`
└── IdpVersionMismatchError
```

`IdpHTTPError.problem: ProblemDetails | None` carries the RFC 7807 envelope (synthesized when the server returns a non-`problem+json` body).

## Polling

`idp-client` deliberately does not ship a `wait_for_job` helper (per the K2:B decision in the spec). Customers orchestrate polling themselves; the canonical pattern:

```python
import time
from idp_client import IdpClient, IdpJobFailed

with IdpClient() as client:
    job = client.submit_job("doc.pdf")
    while job.status in ("queued", "running"):
        time.sleep(2)
        job = client.get_job(job.id)
    if job.status == "failed":
        raise IdpJobFailed(job.error or "extraction failed")
    result = client.get_job_result(job.id)
```

## Examples

[`notebooks/simple/simple-idp.ipynb`](notebooks/simple/simple-idp.ipynb) is a minimal end-to-end notebook: extract a PDF via `IdpClient.extract(..., format="markdown")`, then embed the joined text via `IdpClient.embed(text, model=...)` — IDP serves both extraction and embedding under the same base URL and bearer credential. A single configuration cell at the top exposes every knob; each variable falls back to an env var of the same name.

Required env vars (or edit the config cell):

| Variable          | Default                              | Notes                                                                 |
| ----------------- | ------------------------------------ | --------------------------------------------------------------------- |
| `PDF_PATH`        | `notebooks/simple/moore.pdf`         | Any local PDF the IDP server can read                                 |
| `IDP_BASE_URL`    | `http://localhost:8000`              | Your `ocr-svc` instance — serves extraction _and_ embedding           |
| `IDP_API_KEY`     | _required_                           | Sent as `Authorization: Bearer …` for both calls                      |
| `EMBEDDING_MODEL` | `qwen3-0.6b-doc`                     | IDP **profile id** (not an HF model name) — list with `GET /v1/embedding/models` |

The notebook is **not** executed in CI — it is reference documentation. It does require a reachable IDP backend with both extraction and embedding routes deployed.

## Development

```bash
make install        # uv sync (runtime + dev deps)
make lint           # ruff format + ruff check --fix
make typecheck      # mypy --strict on src/idp_client/
make test           # pytest -m unit (default; respx-mocked)
make test-live      # pytest -m live (against IDP_BASE_URL)
make coverage       # pytest with coverage report
make regen          # regenerate src/idp_client/_generated/ from openapi/openapi.json
make regen-spec     # pull openapi.json from a running api-lib (IDP_OPENAPI_URL)
```

`src/idp_client/_generated/` is committed and excluded from lint, format, and coverage. CI runs `make regen` and fails if the working tree disagrees with the committed snapshot — bring both in sync within the same PR.

The OpenAPI snapshot is hand-authored today (api-lib's extraction routes are still landing). Once api-lib's `/openapi.json` advertises the full surface, switch to `make regen-spec` to refresh.
