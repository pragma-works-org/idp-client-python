"""Synchronous facade over the generated wire client.

Phase 1 covers ``health()``. Phase 2 adds the extraction surface. Construction
is by keyword only: API key resolves from env or explicit param; an injected
``httpx.Client`` is honored as-is for tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, BinaryIO, cast

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
from .compat import CompatMode
from .compat import normalize as _normalize_compat_mode
from .compat import verify as _verify_compat
from .errors import map_response_to_error


class IdpClient:
    """Synchronous client for the ocr-svc IDP REST API.

    Parameters mirror ``httpx.Client`` ergonomics. Pass ``http_client=`` (a
    pre-built :class:`httpx.Client`) in tests to inject a respx transport.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = "http://localhost:8000",
        http_client: httpx.Client | None = None,
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
        self._http: httpx.Client = http_client or httpx.Client(
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
        self._gen.set_httpx_client(self._http)

    def __enter__(self) -> IdpClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying ``httpx.Client``."""
        self._http.close()

    # ----- internal helpers -----------------------------------------------

    def _ensure_compat(self) -> None:
        if self._compat_mode is None or self._compat_done:
            return
        # Late import: defers reading the package's snapshot version until
        # compat-check actually fires, avoiding a circular import at module
        # load time.
        from . import __api_lib_version__

        resp = self._http.get("/health/")
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

    def health(self) -> HealthResponse:
        """Liveness probe. Returns the ``HealthResponse`` reported by the server."""
        self._ensure_compat()
        result = get_health.sync(client=self._gen)
        if result is None:
            # The generator returns None on undocumented status codes when
            # ``raise_on_unexpected_status=False``. Hit the wire directly so
            # we can surface a typed exception with the actual response body.
            resp = self._http.get("/health/")
            self._raise_for_response(resp)
            return cast("HealthResponse", HealthResponse.from_dict(resp.json()))
        return result

    # ----- extraction surface ---------------------------------------------

    def extract(
        self,
        file: str | Path | BinaryIO,
        *,
        format: str | None = None,
        languages: str | list[str] | None = None,
    ) -> ExtractResponse:
        """``POST /v1/extraction/sync`` — synchronous extraction.

        Bypasses the generated function so the file is streamed through
        ``httpx`` rather than being read into memory in one shot.
        """
        self._ensure_compat()
        files, opened = _open_files_for_upload(file)
        try:
            data = _drop_unset(
                {
                    "format": _format_value(format),
                    "languages": _languages_value(languages),
                },
            )
            resp = self._http.post("/v1/extraction/sync", files=files, data=data)
        finally:
            if opened is not None:
                opened.close()
        self._raise_for_response(resp)
        return cast("ExtractResponse", ExtractResponse.from_dict(resp.json()))

    def submit_job(
        self,
        file: str | Path | BinaryIO,
        *,
        format: str | None = None,
        languages: str | list[str] | None = None,
    ) -> ExtractionJobOut:
        """``POST /v1/extraction/jobs`` — submit an async extraction job."""
        self._ensure_compat()
        files, opened = _open_files_for_upload(file)
        try:
            data = _drop_unset(
                {
                    "format": _format_value(format),
                    "languages": _languages_value(languages),
                },
            )
            resp = self._http.post("/v1/extraction/jobs", files=files, data=data)
        finally:
            if opened is not None:
                opened.close()
        self._raise_for_response(resp)
        return cast("ExtractionJobOut", ExtractionJobOut.from_dict(resp.json()))

    def get_job(self, job_id: str) -> ExtractionJobOut:
        """``GET /v1/extraction/jobs/{id}`` — current status of a submitted job."""
        self._ensure_compat()
        wrapped = get_extraction_job.sync_detailed(id=job_id, client=self._gen)
        self._raise_for_response(_synthetic_response_from_wrapper(wrapped))
        result = wrapped.parsed
        if not isinstance(result, ExtractionJobOut):
            raise self._unexpected_payload(wrapped, "ExtractionJobOut")
        return result

    def get_job_result(self, job_id: str) -> ExtractResponse:
        """``GET /v1/extraction/jobs/{id}/result`` — final extraction envelope.

        Only valid when the job is in terminal ``succeeded`` status; the server
        returns a 4xx otherwise (mapped to a typed exception).
        """
        self._ensure_compat()
        wrapped = get_extraction_job_result.sync_detailed(id=job_id, client=self._gen)
        self._raise_for_response(_synthetic_response_from_wrapper(wrapped))
        result = wrapped.parsed
        if not isinstance(result, ExtractResponse):
            raise self._unexpected_payload(wrapped, "ExtractResponse")
        return result

    def cancel_job(self, job_id: str) -> None:
        """``DELETE /v1/extraction/jobs/{id}`` — cancel a queued / running job.

        Returns nothing on success (server replies 204). Already-terminal jobs
        also resolve cleanly per api-lib's planned semantics.
        """
        self._ensure_compat()
        wrapped = cancel_extraction_job.sync_detailed(id=job_id, client=self._gen)
        self._raise_for_response(_synthetic_response_from_wrapper(wrapped))

    # ----- internal helpers (continued) ------------------------------------

    @staticmethod
    def _unexpected_payload(wrapped: object, expected: str) -> Exception:
        return RuntimeError(
            f"Server returned an unexpected payload shape (expected {expected}). "
            f"Status: {getattr(wrapped, 'status_code', '?')}",
        )


# ----- module-level helpers (private) -------------------------------------


def _open_files_for_upload(
    file: str | Path | BinaryIO,
) -> tuple[dict[str, tuple[str, BinaryIO, str]], BinaryIO | None]:
    """Build the ``files=`` mapping for ``httpx.Client.post``.

    Returns the mapping and (when we opened the path ourselves) the handle to
    close after the request lands. Pre-opened streams are passed through
    untouched — the caller owns the lifecycle.
    """
    if isinstance(file, (str, Path)):
        path = Path(file)
        handle: BinaryIO = cast("BinaryIO", path.open("rb"))
        return {"file": (path.name, handle, "application/octet-stream")}, handle
    raw_name = getattr(file, "name", "upload")
    # ``BufferedReader.name`` typically holds the full path. Strip it down to
    # the basename so the multipart `filename=` doesn't leak local paths.
    filename = Path(str(raw_name)).name or "upload"
    return {"file": (filename, file, "application/octet-stream")}, None


def _drop_unset(payload: dict[str, Any]) -> dict[str, Any]:
    """Strip ``None`` values so they don't appear as form fields."""
    return {k: v for k, v in payload.items() if v is not None}


def _format_value(value: str | None) -> str | None:
    """Normalize a ``ResultFormat`` literal/string to the on-the-wire token.

    ``ResultFormat`` is a typing ``Literal`` (the generator emits string-typed
    enums when ``literal_enums: true``), so the value is already wire-shaped.
    The function exists for symmetry with future non-string fields.
    """
    return value


def _languages_value(value: str | list[str] | None) -> str | None:
    """Accept either a comma-joined string or a list and emit the wire form."""
    if value is None:
        return None
    if isinstance(value, list):
        return ",".join(item.strip() for item in value if item.strip()) or None
    return value


def _synthetic_response_from_wrapper(wrapped: object) -> httpx.Response:
    """Re-pack a generator ``Response`` into an ``httpx.Response`` for error mapping.

    The generator's ``Response`` carries the raw bytes, headers, and status
    code; that's everything ``map_response_to_error`` needs.
    """
    status = int(getattr(wrapped, "status_code"))  # noqa: B009 — IntEnum→int
    content = bytes(getattr(wrapped, "content") or b"")  # noqa: B009
    headers = dict(getattr(wrapped, "headers") or {})  # noqa: B009
    return httpx.Response(status_code=status, headers=headers, content=content)
