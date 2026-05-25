"""Tests for the ``idp-client jobs ...`` subcommands."""

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


def _job(status: str = "queued") -> dict[str, object]:
    return {
        "id": "job-XYZ",
        "status": status,
        "page_count": None,
        "error": None,
        "created_at": "2026-05-10T12:00:00Z",
        "started_at": None,
        "completed_at": None,
        "result_url": None,
    }


def _result() -> dict[str, object]:
    return {
        "pages": ["page text"],
        "page_count": 1,
        "processing_time_seconds": 0.2,
        "confidence": None,
    }


def test_jobs_submit_prints_id_in_table(
    runner: CliRunner,
    base_url: str,
    tmp_path: Path,
) -> None:
    file = tmp_path / "doc.pdf"
    file.write_bytes(b"x")
    with respx.mock(base_url=base_url) as router:
        router.post("/v1/extraction/jobs").mock(
            return_value=httpx.Response(202, json=_job()),
        )
        result = runner.invoke(
            app,
            [
                "--api-key",
                "k",
                "--base-url",
                base_url,
                "jobs",
                "submit",
                str(file),
            ],
        )
    assert result.exit_code == 0, result.output
    assert "job-XYZ" in result.output
    assert "queued" in result.output


def test_jobs_status_table_layout(runner: CliRunner, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        router.get("/v1/extraction/jobs/job-XYZ").mock(
            return_value=httpx.Response(200, json=_job("succeeded")),
        )
        result = runner.invoke(
            app,
            ["--api-key", "k", "--base-url", base_url, "jobs", "status", "job-XYZ"],
        )
    assert result.exit_code == 0, result.output
    assert "id" in result.output
    assert "status" in result.output
    assert "succeeded" in result.output


def test_jobs_status_json(runner: CliRunner, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        router.get("/v1/extraction/jobs/job-XYZ").mock(
            return_value=httpx.Response(200, json=_job("running")),
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
                "jobs",
                "status",
                "job-XYZ",
            ],
        )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output.strip())
    assert payload["id"] == "job-XYZ"
    assert payload["status"] == "running"


def test_jobs_result_writes_to_out_file(
    runner: CliRunner,
    base_url: str,
    tmp_path: Path,
) -> None:
    out = tmp_path / "out.txt"
    with respx.mock(base_url=base_url) as router:
        router.get("/v1/extraction/jobs/job-XYZ/result").mock(
            return_value=httpx.Response(200, json=_result()),
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
                "jobs",
                "result",
                "job-XYZ",
                "--out",
                str(out),
            ],
        )
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert "page text" in out.read_text()


def test_jobs_cancel_success(runner: CliRunner, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        router.delete("/v1/extraction/jobs/job-XYZ").mock(
            return_value=httpx.Response(204),
        )
        result = runner.invoke(
            app,
            ["--api-key", "k", "--base-url", base_url, "jobs", "cancel", "job-XYZ"],
        )
    assert result.exit_code == 0, result.output
    assert "cancelled: job-XYZ" in result.output


def test_jobs_cancel_404_exits_non_zero(runner: CliRunner, base_url: str) -> None:
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
        result = runner.invoke(
            app,
            ["--api-key", "k", "--base-url", base_url, "jobs", "cancel", "missing"],
        )
    assert result.exit_code != 0
    assert "error:" in result.output
