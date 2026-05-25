"""Async parity tests for ``AsyncIdpClient``.

Mirrors ``test_client_*`` and ``test_compat_check`` for the async surface.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

from idp_client import AsyncIdpClient
from idp_client.errors import (
    IdpAuthError,
    IdpNotFoundError,
    IdpServerError,
    IdpVersionMismatchError,
)

# ----- health --------------------------------------------------------------


async def test_async_health_returns_status(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url, assert_all_called=True) as router:
        route = router.get("/health/").mock(
            return_value=httpx.Response(200, json={"status": "ok", "version": "0.1.0"}),
        )
        async with AsyncIdpClient(api_key=api_key, base_url=base_url) as client:
            result = await client.health()
    assert getattr(result.status, "value", str(result.status)) == "ok"
    assert result.version == "0.1.0"
    sent = route.calls.last.request
    assert sent.headers["x-api-key"] == api_key


async def test_async_health_5xx_raises(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        router.get("/health/").mock(
            return_value=httpx.Response(503, content=b"down"),
        )
        async with AsyncIdpClient(api_key=api_key, base_url=base_url) as client:
            with pytest.raises(IdpServerError):
                await client.health()


# ----- auth ---------------------------------------------------------------


async def test_async_constructor_without_key_raises() -> None:
    with pytest.raises(IdpAuthError):
        AsyncIdpClient(base_url="http://api.test.local")


# ----- compat-check (Q1:A: awaited) ---------------------------------------


async def test_async_compat_check_minor_passes(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url, assert_all_called=False) as router:
        router.get("/health/").mock(
            return_value=httpx.Response(200, json={"status": "ok", "version": "0.1.7"}),
        )
        async with AsyncIdpClient(
            api_key=api_key,
            base_url=base_url,
            compat_check=True,
        ) as client:
            await client.health()


async def test_async_compat_check_minor_raises_on_major_bump(
    api_key: str,
    base_url: str,
) -> None:
    with respx.mock(base_url=base_url, assert_all_called=False) as router:
        router.get("/health/").mock(
            return_value=httpx.Response(200, json={"status": "ok", "version": "1.0.0"}),
        )
        async with AsyncIdpClient(
            api_key=api_key,
            base_url=base_url,
            compat_check="minor",
        ) as client:
            with pytest.raises(IdpVersionMismatchError):
                await client.health()


async def test_async_compat_check_only_runs_once(api_key: str, base_url: str) -> None:
    """The lazy probe should fire on the first request, not on every call."""
    with respx.mock(base_url=base_url, assert_all_called=False) as router:
        health_route = router.get("/health/").mock(
            return_value=httpx.Response(200, json={"status": "ok", "version": "0.1.0"}),
        )
        async with AsyncIdpClient(
            api_key=api_key,
            base_url=base_url,
            compat_check=True,
        ) as client:
            await client.health()
            await client.health()
            await client.health()
        # 3 user health() calls + 1 compat probe = 4 total. Compat itself is
        # idempotent — would-be probes after the first are short-circuited.
        assert health_route.call_count == 4


# ----- extraction surface --------------------------------------------------


async def test_async_extract_streams_path(
    api_key: str,
    base_url: str,
    tmp_path: Path,
) -> None:
    file = tmp_path / "doc.pdf"
    file.write_bytes(b"%PDF-1.4 fake")
    with respx.mock(base_url=base_url) as router:
        route = router.post("/v1/extraction/sync").mock(
            return_value=httpx.Response(
                200,
                json={
                    "pages": ["a", "b"],
                    "page_count": 2,
                    "processing_time_seconds": 0.1,
                    "confidence": None,
                },
            ),
        )
        async with AsyncIdpClient(api_key=api_key, base_url=base_url) as client:
            response = await client.extract(file, format="markdown")
    assert response.page_count == 2
    body = route.calls.last.request.content
    assert b"%PDF-1.4 fake" in body


async def test_async_submit_job(api_key: str, base_url: str, tmp_path: Path) -> None:
    file = tmp_path / "doc.pdf"
    file.write_bytes(b"x")
    descriptor = {
        "id": "job-async",
        "status": "queued",
        "page_count": None,
        "error": None,
        "created_at": "2026-05-10T12:00:00Z",
        "started_at": None,
        "completed_at": None,
        "result_url": None,
    }
    with respx.mock(base_url=base_url) as router:
        router.post("/v1/extraction/jobs").mock(
            return_value=httpx.Response(202, json=descriptor),
        )
        async with AsyncIdpClient(api_key=api_key, base_url=base_url) as client:
            job = await client.submit_job(file)
    assert job.id == "job-async"


async def test_async_get_job(api_key: str, base_url: str) -> None:
    descriptor = {
        "id": "job-XYZ",
        "status": "running",
        "page_count": None,
        "error": None,
        "created_at": "2026-05-10T12:00:00Z",
        "started_at": "2026-05-10T12:00:01Z",
        "completed_at": None,
        "result_url": None,
    }
    with respx.mock(base_url=base_url) as router:
        router.get("/v1/extraction/jobs/job-XYZ").mock(
            return_value=httpx.Response(200, json=descriptor),
        )
        async with AsyncIdpClient(api_key=api_key, base_url=base_url) as client:
            job = await client.get_job("job-XYZ")
    assert job.status == "running"


async def test_async_get_job_404(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        router.get("/v1/extraction/jobs/missing").mock(
            return_value=httpx.Response(
                404,
                headers={"content-type": "application/problem+json"},
                content=json.dumps(
                    {
                        "type": "about:blank",
                        "title": "Not Found",
                        "status": 404,
                        "detail": "no such job",
                    },
                ).encode(),
            ),
        )
        async with AsyncIdpClient(api_key=api_key, base_url=base_url) as client:
            with pytest.raises(IdpNotFoundError):
                await client.get_job("missing")


async def test_async_get_job_result(api_key: str, base_url: str) -> None:
    envelope = {
        "pages": ["only"],
        "page_count": 1,
        "processing_time_seconds": 0.5,
        "confidence": None,
    }
    with respx.mock(base_url=base_url) as router:
        router.get("/v1/extraction/jobs/job-XYZ/result").mock(
            return_value=httpx.Response(200, json=envelope),
        )
        async with AsyncIdpClient(api_key=api_key, base_url=base_url) as client:
            response = await client.get_job_result("job-XYZ")
    assert response.pages == ["only"]


async def test_async_cancel_job(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        route = router.delete("/v1/extraction/jobs/job-XYZ").mock(
            return_value=httpx.Response(204),
        )
        async with AsyncIdpClient(api_key=api_key, base_url=base_url) as client:
            assert await client.cancel_job("job-XYZ") is None
    assert route.called
