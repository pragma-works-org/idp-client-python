"""Tests for ``IdpClient.extract`` (synchronous extraction)."""

from __future__ import annotations

import io
import json
from pathlib import Path

import httpx
import pytest
import respx

from idp_client import IdpClient
from idp_client.errors import IdpServerError, IdpValidationError


def _ok_extract_response() -> dict[str, object]:
    return {
        "pages": ["page one", "page two"],
        "page_count": 2,
        "processing_time_seconds": 1.25,
        "confidence": None,
    }


def test_extract_happy_path_with_pre_opened_stream(api_key: str, base_url: str) -> None:
    payload = b"%PDF-1.4 fake"
    fake = io.BytesIO(payload)
    fake.name = "doc.pdf"
    with respx.mock(base_url=base_url) as router:
        route = router.post("/v1/extraction/sync").mock(
            return_value=httpx.Response(200, json=_ok_extract_response()),
        )
        with IdpClient(api_key=api_key, base_url=base_url) as client:
            response = client.extract(fake, format="markdown", languages="en,es")
    assert response.page_count == 2
    assert response.pages == ["page one", "page two"]
    sent = route.calls.last.request
    assert sent.headers["x-api-key"] == api_key
    assert sent.headers["content-type"].startswith("multipart/form-data; boundary=")


def test_extract_streams_path(
    api_key: str,
    base_url: str,
    tmp_path: Path,
) -> None:
    file = tmp_path / "doc.pdf"
    file.write_bytes(b"%PDF body bytes")
    with respx.mock(base_url=base_url) as router:
        route = router.post("/v1/extraction/sync").mock(
            return_value=httpx.Response(200, json=_ok_extract_response()),
        )
        with IdpClient(api_key=api_key, base_url=base_url) as client:
            client.extract(file)
    assert route.called


def test_extract_drops_none_form_fields(
    api_key: str,
    base_url: str,
    tmp_path: Path,
) -> None:
    file = tmp_path / "doc.pdf"
    file.write_bytes(b"x")
    with respx.mock(base_url=base_url) as router:
        route = router.post("/v1/extraction/sync").mock(
            return_value=httpx.Response(200, json=_ok_extract_response()),
        )
        with IdpClient(api_key=api_key, base_url=base_url) as client:
            client.extract(file)
    body = route.calls.last.request.content
    # Neither field name should appear in the body when both are unset.
    assert b'name="format"' not in body
    assert b'name="languages"' not in body


def test_extract_languages_list_is_joined(
    api_key: str,
    base_url: str,
    tmp_path: Path,
) -> None:
    file = tmp_path / "doc.pdf"
    file.write_bytes(b"x")
    with respx.mock(base_url=base_url) as router:
        route = router.post("/v1/extraction/sync").mock(
            return_value=httpx.Response(200, json=_ok_extract_response()),
        )
        with IdpClient(api_key=api_key, base_url=base_url) as client:
            client.extract(file, languages=["en", " es ", ""])
    body = route.calls.last.request.content
    assert b'name="languages"' in body
    assert b"en,es" in body


def test_extract_4xx_raises_validation_error(
    api_key: str,
    base_url: str,
    tmp_path: Path,
) -> None:
    file = tmp_path / "doc.pdf"
    file.write_bytes(b"x")
    with respx.mock(base_url=base_url) as router:
        router.post("/v1/extraction/sync").mock(
            return_value=httpx.Response(
                422,
                headers={"content-type": "application/problem+json"},
                content=json.dumps(
                    {
                        "type": "https://errors.idp/validation",
                        "title": "Validation",
                        "status": 422,
                        "detail": "format unsupported",
                    },
                ).encode(),
            ),
        )
        with IdpClient(api_key=api_key, base_url=base_url) as client:
            with pytest.raises(IdpValidationError):
                client.extract(file, format="bogus")


def test_extract_5xx_raises_server_error(
    api_key: str,
    base_url: str,
    tmp_path: Path,
) -> None:
    file = tmp_path / "doc.pdf"
    file.write_bytes(b"x")
    with respx.mock(base_url=base_url) as router:
        router.post("/v1/extraction/sync").mock(
            return_value=httpx.Response(503, content=b"down"),
        )
        with IdpClient(api_key=api_key, base_url=base_url) as client:
            with pytest.raises(IdpServerError):
                client.extract(file)
