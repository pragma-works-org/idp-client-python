"""Asynchronous facade. Parallel surface to :class:`IdpClient`.

Per Q1:A, ``_ensure_compat`` is ``async def`` here and is awaited from every
public method. ``compat.verify`` itself stays a pure sync function.

Mechanical duplication of ``client.py`` (S2:A) — no shared core. The dual is
intentional: tracebacks stay readable, no abstraction tax, and each facade
owns its own httpx lifecycle.
"""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO, cast

import httpx

from ._generated.api.extraction import (
    cancel_extraction_job,
    get_extraction_job,
    get_extraction_job_result,
)
from ._generated.api.health import get_health
from ._generated.client import AuthenticatedClient
from ._generated.models import (
    ExtractionJobOut,
    ExtractResponse,
    HealthResponse,
)
from ._version import __version__
from .auth import resolve_api_key
from .client import (
    _drop_unset,
    _format_value,
    _languages_value,
    _open_files_for_upload,
    _synthetic_response_from_wrapper,
)
from .compat import CompatMode
from .compat import normalize as _normalize_compat_mode
from .compat import verify as _verify_compat
from .errors import map_response_to_error


class AsyncIdpClient:
    """Asynchronous client for the ocr-svc IDP REST API.

    Mirrors :class:`idp_client.IdpClient` method-for-method; every public
    method is ``async``. Use as an async context manager so the underlying
    ``httpx.AsyncClient`` closes cleanly.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = "http://localhost:8000",
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
        compat_check: CompatMode = False,
    ) -> None:
        self._api_key = resolve_api_key(api_key)
        self._compat_mode = _normalize_compat_mode(compat_check)
        self._compat_done = False
        self._base_url = base_url
        ua = f"idp-client-py/{__version__}"
        headers = {
            "X-Api-Key": self._api_key,
            "User-Agent": ua,
            "X-Idp-Client": f"py/{__version__}",
        }
        self._http: httpx.AsyncClient = http_client or httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
        )
        self._gen = AuthenticatedClient(
            base_url=base_url,
            token=self._api_key,
            prefix="",
            auth_header_name="X-Api-Key",
            timeout=httpx.Timeout(timeout),
        )
        self._gen.set_async_httpx_client(self._http)

    async def __aenter__(self) -> AsyncIdpClient:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying ``httpx.AsyncClient``."""
        await self._http.aclose()

    # ----- internal helpers -----------------------------------------------

    async def _ensure_compat(self) -> None:
        if self._compat_mode is None or self._compat_done:
            return
        # Late import: avoids the package-level circular at module load time.
        from . import __api_lib_version__

        resp = await self._http.get("/health/")
        if err := map_response_to_error(resp):
            raise err
        body = resp.json()
        server_version = str(body["version"])
        _verify_compat(server_version, __api_lib_version__, self._compat_mode)
        self._compat_done = True

    def _raise_for_response(self, resp: httpx.Response) -> None:
        if err := map_response_to_error(resp):
            raise err

    # ----- public surface --------------------------------------------------

    async def health(self) -> HealthResponse:
        """``GET /health/`` — liveness probe."""
        await self._ensure_compat()
        result = await get_health.asyncio(client=self._gen)
        if result is None:
            resp = await self._http.get("/health/")
            self._raise_for_response(resp)
            return cast("HealthResponse", HealthResponse.from_dict(resp.json()))
        return result

    async def extract(
        self,
        file: str | Path | BinaryIO,
        *,
        format: str | None = None,
        languages: str | list[str] | None = None,
    ) -> ExtractResponse:
        """``POST /v1/extraction/sync`` — async streaming-multipart upload."""
        await self._ensure_compat()
        files, opened = _open_files_for_upload(file)
        try:
            data = _drop_unset(
                {
                    "format": _format_value(format),
                    "languages": _languages_value(languages),
                },
            )
            resp = await self._http.post("/v1/extraction/sync", files=files, data=data)
        finally:
            if opened is not None:
                opened.close()
        self._raise_for_response(resp)
        return cast("ExtractResponse", ExtractResponse.from_dict(resp.json()))

    async def submit_job(
        self,
        file: str | Path | BinaryIO,
        *,
        format: str | None = None,
        languages: str | list[str] | None = None,
    ) -> ExtractionJobOut:
        """``POST /v1/extraction/jobs`` — async streaming submit."""
        await self._ensure_compat()
        files, opened = _open_files_for_upload(file)
        try:
            data = _drop_unset(
                {
                    "format": _format_value(format),
                    "languages": _languages_value(languages),
                },
            )
            resp = await self._http.post("/v1/extraction/jobs", files=files, data=data)
        finally:
            if opened is not None:
                opened.close()
        self._raise_for_response(resp)
        return cast("ExtractionJobOut", ExtractionJobOut.from_dict(resp.json()))

    async def get_job(self, job_id: str) -> ExtractionJobOut:
        """``GET /v1/extraction/jobs/{id}`` — async status fetch."""
        await self._ensure_compat()
        wrapped = await get_extraction_job.asyncio_detailed(id=job_id, client=self._gen)
        self._raise_for_response(_synthetic_response_from_wrapper(wrapped))
        result = wrapped.parsed
        if not isinstance(result, ExtractionJobOut):
            raise _unexpected_payload(wrapped, "ExtractionJobOut")
        return result

    async def get_job_result(self, job_id: str) -> ExtractResponse:
        """``GET /v1/extraction/jobs/{id}/result`` — async result fetch."""
        await self._ensure_compat()
        wrapped = await get_extraction_job_result.asyncio_detailed(id=job_id, client=self._gen)
        self._raise_for_response(_synthetic_response_from_wrapper(wrapped))
        result = wrapped.parsed
        if not isinstance(result, ExtractResponse):
            raise _unexpected_payload(wrapped, "ExtractResponse")
        return result

    async def cancel_job(self, job_id: str) -> None:
        """``DELETE /v1/extraction/jobs/{id}`` — async cancel."""
        await self._ensure_compat()
        wrapped = await cancel_extraction_job.asyncio_detailed(id=job_id, client=self._gen)
        self._raise_for_response(_synthetic_response_from_wrapper(wrapped))


def _unexpected_payload(wrapped: object, expected: str) -> Exception:
    return RuntimeError(
        f"Server returned an unexpected payload shape (expected {expected}). "
        f"Status: {getattr(wrapped, 'status_code', '?')}",
    )
