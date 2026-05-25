"""Tests for the ``idp-client extract`` Typer command."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx
from typer.testing import CliRunner

from idp_client.cli import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _ok() -> dict[str, object]:
    return {
        "pages": ["alpha", "beta"],
        "page_count": 2,
        "processing_time_seconds": 0.42,
        "confidence": None,
    }


def test_extract_default_output_is_raw_pages(
    runner: CliRunner,
    base_url: str,
    tmp_path: Path,
) -> None:
    file = tmp_path / "doc.pdf"
    file.write_bytes(b"x")
    with respx.mock(base_url=base_url) as router:
        router.post("/v1/extraction/sync").mock(
            return_value=httpx.Response(200, json=_ok()),
        )
        result = runner.invoke(
            app,
            [
                "--api-key",
                "k",
                "--base-url",
                base_url,
                "--output",
                "raw",
                "extract",
                str(file),
            ],
        )
    assert result.exit_code == 0, result.output
    assert "alpha" in result.output
    assert "beta" in result.output


def test_extract_json_output(
    runner: CliRunner,
    base_url: str,
    tmp_path: Path,
) -> None:
    file = tmp_path / "doc.pdf"
    file.write_bytes(b"x")
    with respx.mock(base_url=base_url) as router:
        router.post("/v1/extraction/sync").mock(
            return_value=httpx.Response(200, json=_ok()),
        )
        result = runner.invoke(
            app,
            [
                "--api-key",
                "k",
                "--base-url",
                base_url,
                "--output",
                "json",
                "extract",
                str(file),
            ],
        )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output.strip())
    assert payload["page_count"] == 2
    assert payload["pages"] == ["alpha", "beta"]


def test_extract_failure_surfaces_error(
    runner: CliRunner,
    base_url: str,
    tmp_path: Path,
) -> None:
    file = tmp_path / "doc.pdf"
    file.write_bytes(b"x")
    with respx.mock(base_url=base_url) as router:
        router.post("/v1/extraction/sync").mock(
            return_value=httpx.Response(500, content=b"boom"),
        )
        result = runner.invoke(
            app,
            ["--api-key", "k", "--base-url", base_url, "extract", str(file)],
        )
    assert result.exit_code != 0
    assert "error:" in result.output


def test_extract_passes_format_and_languages(
    runner: CliRunner,
    base_url: str,
    tmp_path: Path,
) -> None:
    file = tmp_path / "doc.pdf"
    file.write_bytes(b"x")
    with respx.mock(base_url=base_url) as router:
        route = router.post("/v1/extraction/sync").mock(
            return_value=httpx.Response(200, json=_ok()),
        )
        result = runner.invoke(
            app,
            [
                "--api-key",
                "k",
                "--base-url",
                base_url,
                "extract",
                str(file),
                "--format",
                "json",
                "--languages",
                "en,es",
            ],
        )
    assert result.exit_code == 0, result.output
    body = route.calls.last.request.content
    assert b'name="format"' in body
    assert b"json" in body
    assert b"en,es" in body
