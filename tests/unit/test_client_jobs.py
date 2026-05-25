"""Tests for ``IdpClient.submit_job``, ``get_job``, ``get_job_result``, ``cancel_job``."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

from idp_client import IdpClient
from idp_client.errors import IdpNotFoundError


def _job_descriptor(status: str = "queued") -> dict[str, object]:
    return {
        "id": "job-abc123",
        "status": status,
        "page_count": None,
        "error": None,
        "created_at": "2026-05-10T12:00:00Z",
        "started_at": None,
        "completed_at": None,
        "result_url": None,
    }


def _result_envelope() -> dict[str, object]:
    return {
        "pages": ["only page"],
        "page_count": 1,
        "processing_time_seconds": 0.5,
        "confidence": None,
    }


def test_submit_job_returns_descriptor(
    api_key: str,
    base_url: str,
    tmp_path: Path,
) -> None:
    file = tmp_path / "doc.pdf"
    file.write_bytes(b"x")
    with respx.mock(base_url=base_url) as router:
        route = router.post("/v1/extraction/jobs").mock(
            return_value=httpx.Response(202, json=_job_descriptor()),
        )
        with IdpClient(api_key=api_key, base_url=base_url) as client:
            descriptor = client.submit_job(file, format="markdown")
    assert descriptor.id == "job-abc123"
    sent = route.calls.last.request
    assert sent.headers["content-type"].startswith("multipart/form-data; boundary=")


def test_get_job_routes_through_id(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        route = router.get("/v1/extraction/jobs/job-abc123").mock(
            return_value=httpx.Response(200, json=_job_descriptor("running")),
        )
        with IdpClient(api_key=api_key, base_url=base_url) as client:
            descriptor = client.get_job("job-abc123")
    assert descriptor.status == "running"
    assert route.called


def test_get_job_404_raises_not_found(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        router.get("/v1/extraction/jobs/missing").mock(
            return_value=httpx.Response(
                404,
                headers={"content-type": "application/problem+json"},
                content=json.dumps(
                    {
                        "type": "https://errors.idp/notfound",
                        "title": "Not Found",
                        "status": 404,
                        "detail": "no such job",
                    },
                ).encode(),
            ),
        )
        with IdpClient(api_key=api_key, base_url=base_url) as client:
            with pytest.raises(IdpNotFoundError):
                client.get_job("missing")


def test_get_job_result_returns_envelope(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        router.get("/v1/extraction/jobs/job-abc123/result").mock(
            return_value=httpx.Response(200, json=_result_envelope()),
        )
        with IdpClient(api_key=api_key, base_url=base_url) as client:
            response = client.get_job_result("job-abc123")
    assert response.pages == ["only page"]


def test_cancel_job_returns_none_on_204(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        route = router.delete("/v1/extraction/jobs/job-abc123").mock(
            return_value=httpx.Response(204),
        )
        with IdpClient(api_key=api_key, base_url=base_url) as client:
            assert client.cancel_job("job-abc123") is None
    assert route.called


def test_cancel_job_404_raises(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        router.delete("/v1/extraction/jobs/missing").mock(
            return_value=httpx.Response(
                404,
                headers={"content-type": "application/problem+json"},
                content=json.dumps(
                    {
                        "type": "https://errors.idp/notfound",
                        "title": "Not Found",
                        "status": 404,
                        "detail": "no such job",
                    },
                ).encode(),
            ),
        )
        with IdpClient(api_key=api_key, base_url=base_url) as client:
            with pytest.raises(IdpNotFoundError):
                client.cancel_job("missing")
