"""Tests for ``IdpClient.health()`` and the Authorization Bearer header wiring."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from idp_client import IdpClient
from idp_client.errors import IdpAuthError, IdpServerError, IdpVersionMismatchError


def _build_client(api_key: str, base_url: str) -> IdpClient:
    return IdpClient(api_key=api_key, base_url=base_url)


def test_health_returns_status(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url, assert_all_called=True) as router:
        route = router.get("/health/").mock(
            return_value=httpx.Response(200, json={"status": "ok", "version": "0.1.0"}),
        )
        client = _build_client(api_key, base_url)
        result = client.health()
        client.close()

    assert getattr(result.status, "value", str(result.status)) == "ok"
    assert result.version == "0.1.0"
    sent = route.calls.last.request
    assert sent.headers["authorization"] == f"Bearer {api_key}"
    assert sent.headers["user-agent"].startswith("idp-client-py/")
    assert sent.headers["x-idp-client"].startswith("py/")


def test_health_4xx_raises_typed_error(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        router.get("/health/").mock(
            return_value=httpx.Response(
                401,
                headers={"content-type": "application/problem+json"},
                content=json.dumps(
                    {
                        "type": "https://errors.idp/auth",
                        "title": "Unauthorized",
                        "status": 401,
                        "detail": "bad key",
                    },
                ).encode(),
            ),
        )
        client = _build_client(api_key, base_url)
        with pytest.raises(IdpAuthError) as excinfo:
            client.health()
        client.close()
    assert excinfo.value.status == 401
    assert excinfo.value.problem is not None
    assert excinfo.value.problem.detail == "bad key"


def test_health_5xx_raises_server_error(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        router.get("/health/").mock(
            return_value=httpx.Response(503, content=b"upstream down"),
        )
        client = _build_client(api_key, base_url)
        with pytest.raises(IdpServerError):
            client.health()
        client.close()


def test_compat_check_off_skips_extra_request(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url, assert_all_called=False) as router:
        health_route = router.get("/health/").mock(
            return_value=httpx.Response(200, json={"status": "ok", "version": "0.1.0"}),
        )
        client = IdpClient(api_key=api_key, base_url=base_url, compat_check=False)
        client.health()
        client.close()
    # Single call, no eager probe.
    assert health_route.call_count == 1


def test_compat_check_minor_passes_for_same_minor(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url, assert_all_called=False) as router:
        router.get("/health/").mock(
            return_value=httpx.Response(200, json={"status": "ok", "version": "0.1.7"}),
        )
        client = IdpClient(api_key=api_key, base_url=base_url, compat_check=True)
        client.health()  # should not raise
        client.close()


def test_compat_check_minor_raises_on_major_bump(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url, assert_all_called=False) as router:
        router.get("/health/").mock(
            return_value=httpx.Response(200, json={"status": "ok", "version": "1.0.0"}),
        )
        client = IdpClient(api_key=api_key, base_url=base_url, compat_check="minor")
        with pytest.raises(IdpVersionMismatchError):
            client.health()
        client.close()


def test_constructor_without_api_key_or_env_raises() -> None:
    with pytest.raises(IdpAuthError):
        IdpClient(base_url="http://api.test.local")
