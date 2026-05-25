"""Streaming-multipart upload contract tests.

These exercise ``IdpClient.extract`` against a respx body matcher, asserting
that:

    1. ``Content-Type`` starts with ``multipart/form-data; boundary=``
    2. The captured request body contains the file's bytes (so we know the
       upload was actually written, not silently dropped).
    3. The boundary appears in the body (sanity-check of multipart shape).
"""

from __future__ import annotations

from pathlib import Path

import httpx
import respx

from idp_client import IdpClient

_SYNTHETIC_PDF = b"%PDF-1.4\n1 0 obj <<>> endobj\ntrailer <<>> startxref 0 %%EOF\n"


def _ok() -> dict[str, object]:
    return {
        "pages": ["p1"],
        "page_count": 1,
        "processing_time_seconds": 0.1,
        "confidence": None,
    }


def test_upload_sends_multipart_with_file_bytes(
    api_key: str,
    base_url: str,
    tmp_path: Path,
) -> None:
    file = tmp_path / "synth.pdf"
    file.write_bytes(_SYNTHETIC_PDF)
    with respx.mock(base_url=base_url) as router:
        route = router.post("/v1/extraction/sync").mock(
            return_value=httpx.Response(200, json=_ok()),
        )
        with IdpClient(api_key=api_key, base_url=base_url) as client:
            client.extract(file)

    request = route.calls.last.request
    content_type = request.headers["content-type"]
    assert content_type.startswith("multipart/form-data; boundary=")

    boundary = content_type.split("boundary=", 1)[1]
    body = request.content
    assert boundary.encode() in body
    assert _SYNTHETIC_PDF in body
    assert b'name="file"' in body
    assert b'filename="synth.pdf"' in body


def test_upload_handles_pre_opened_handle(
    api_key: str,
    base_url: str,
    tmp_path: Path,
) -> None:
    file = tmp_path / "passthrough.pdf"
    file.write_bytes(_SYNTHETIC_PDF)
    with respx.mock(base_url=base_url) as router:
        route = router.post("/v1/extraction/sync").mock(
            return_value=httpx.Response(200, json=_ok()),
        )
        with file.open("rb") as fh, IdpClient(api_key=api_key, base_url=base_url) as client:
            client.extract(fh)

    body = route.calls.last.request.content
    assert _SYNTHETIC_PDF in body
    # File handle name carries through to the multipart filename.
    assert b'filename="passthrough.pdf"' in body
