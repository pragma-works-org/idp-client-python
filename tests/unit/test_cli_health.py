"""Tests for the Typer CLI: ``idp-client health`` / ``version``."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from typer.testing import CliRunner

from idp_client.cli import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_health_table_output(runner: CliRunner, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        router.get("/health/").mock(
            return_value=httpx.Response(200, json={"status": "ok", "version": "0.1.0"}),
        )
        result = runner.invoke(
            app,
            [
                "--api-key",
                "k",
                "--base-url",
                base_url,
                "health",
            ],
        )
    assert result.exit_code == 0, result.output
    assert "status:" in result.output
    assert "version:" in result.output
    assert "0.1.0" in result.output


def test_health_json_output(runner: CliRunner, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        router.get("/health/").mock(
            return_value=httpx.Response(200, json={"status": "ok", "version": "0.1.0"}),
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
                "health",
            ],
        )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output.strip())
    assert payload == {"status": "ok", "version": "0.1.0"}


def test_health_raw_output(runner: CliRunner, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        router.get("/health/").mock(
            return_value=httpx.Response(200, json={"status": "ok", "version": "0.1.0"}),
        )
        result = runner.invoke(
            app,
            ["--api-key", "k", "--base-url", base_url, "--output", "raw", "health"],
        )
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "ok"


def test_health_failure_exits_non_zero(runner: CliRunner, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        router.get("/health/").mock(
            return_value=httpx.Response(500, content=b"down"),
        )
        result = runner.invoke(
            app,
            ["--api-key", "k", "--base-url", base_url, "health"],
        )
    assert result.exit_code != 0
    assert "error:" in result.output


def test_invalid_output_flag_rejected(runner: CliRunner, base_url: str) -> None:
    result = runner.invoke(
        app,
        ["--api-key", "k", "--base-url", base_url, "--output", "yaml", "health"],
    )
    assert result.exit_code != 0


def test_version_command_table(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--api-key", "k", "version"])
    assert result.exit_code == 0
    assert "idp-client" in result.output
    assert "snapshot" in result.output


def test_version_command_json(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--api-key", "k", "--output", "json", "version"])
    assert result.exit_code == 0
    payload = json.loads(result.output.strip())
    assert "client" in payload and "api_lib_snapshot" in payload


def test_health_picks_up_env_api_key(
    runner: CliRunner,
    base_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("IDP_API_KEY", "from-env")
    with respx.mock(base_url=base_url) as router:
        route = router.get("/health/").mock(
            return_value=httpx.Response(200, json={"status": "ok", "version": "0.1.0"}),
        )
        result = runner.invoke(app, ["--base-url", base_url, "health"])
    assert result.exit_code == 0, result.output
    assert route.calls.last.request.headers["authorization"] == "Bearer from-env"
