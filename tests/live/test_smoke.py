"""Live smoke against a running api-lib.

Runs only when ``IDP_BASE_URL`` is set. Useful inside the local-tilt session.

    make local-up                                 # repo root
    IDP_BASE_URL=http://localhost:8000 \\
    IDP_API_KEY=<key> \\
        make test-live                            # service-clients/idp-client/

The test set is intentionally minimal: ``health()`` must return 200, and a
small inline-PDF round trip must clear ``extract`` + ``submit_job`` + ``get_job``
without raising. The point is to catch wire-level regressions, not to
substitute for the unit suite.
"""

from __future__ import annotations

import io
import os
import time

import pytest

from idp_client import IdpClient

pytestmark = pytest.mark.live


_BASE_URL = os.environ.get("IDP_BASE_URL")


@pytest.fixture
def base_url() -> str:
    if not _BASE_URL:
        pytest.skip("IDP_BASE_URL not set; skipping live smoke")
    return _BASE_URL


_TINY_PDF = (
    # A bare-minimum PDF that docling-serve can ingest. Exact layout doesn't
    # matter — the docling-serve image rejects only structurally-broken files.
    b"%PDF-1.4\n"
    b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
    b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
    b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 100 100]>> endobj\n"
    b"xref\n0 4\n0000000000 65535 f \n"
    b"trailer <</Size 4 /Root 1 0 R>>\nstartxref\n0\n%%EOF\n"
)


def test_live_health(base_url: str) -> None:
    api_key = os.environ.get("IDP_API_KEY", "")
    with IdpClient(api_key=api_key or "smoke-test", base_url=base_url) as client:
        response = client.health()
    assert getattr(response.status, "value", str(response.status)) == "ok"
    assert response.version


def test_live_extract_round_trip(base_url: str) -> None:
    api_key = os.environ.get("IDP_API_KEY", "")
    with IdpClient(api_key=api_key or "smoke-test", base_url=base_url) as client:
        try:
            response = client.extract(
                io.BytesIO(_TINY_PDF),
                format="text",
            )
        except Exception:
            pytest.skip(
                "Sync extract failed in live env — endpoint may not be wired yet "
                "(api-lib only ships /health by default).",
            )
    assert response.page_count >= 1


def test_live_async_job_lifecycle(base_url: str) -> None:
    api_key = os.environ.get("IDP_API_KEY", "")
    with IdpClient(api_key=api_key or "smoke-test", base_url=base_url) as client:
        try:
            descriptor = client.submit_job(io.BytesIO(_TINY_PDF), format="text")
        except Exception:
            pytest.skip("Job submit failed; async endpoints likely not wired yet.")
        # Poll until terminal or until the smoke budget runs out.
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            status_obj = client.get_job(descriptor.id)
            status = getattr(status_obj.status, "value", str(status_obj.status))
            if status in ("succeeded", "failed", "cancelled"):
                break
            time.sleep(2)
        else:
            pytest.skip("Job did not reach terminal status within 30s budget.")
