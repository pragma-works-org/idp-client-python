"""Tests for ``idp_client.errors.map_response_to_error``."""

from __future__ import annotations

import json

import httpx
import pytest

from idp_client.errors import (
    IdpAuthError,
    IdpHTTPError,
    IdpNotFoundError,
    IdpServerError,
    IdpValidationError,
    map_response_to_error,
)


def _problem_response(status: int, body: dict[str, object]) -> httpx.Response:
    return httpx.Response(
        status_code=status,
        headers={"content-type": "application/problem+json"},
        content=json.dumps(body).encode(),
    )


def test_success_returns_none() -> None:
    resp = httpx.Response(status_code=200, content=b"{}")
    assert map_response_to_error(resp) is None


@pytest.mark.parametrize(
    "status, expected_cls",
    [
        (401, IdpAuthError),
        (403, IdpAuthError),
        (404, IdpNotFoundError),
        (422, IdpValidationError),
        (500, IdpServerError),
        (503, IdpServerError),
        (418, IdpHTTPError),
    ],
)
def test_status_maps_to_typed_exception(
    status: int,
    expected_cls: type[IdpHTTPError],
) -> None:
    resp = _problem_response(
        status,
        {
            "type": "https://errors.idp/test",
            "title": "Test failure",
            "status": status,
            "detail": "boom",
        },
    )
    err = map_response_to_error(resp)
    assert err is not None
    assert isinstance(err, expected_cls)
    assert err.status == status
    assert err.problem is not None
    assert err.problem.type == "https://errors.idp/test"
    assert err.problem.detail == "boom"


def test_problem_extra_carries_through() -> None:
    resp = _problem_response(
        422,
        {
            "type": "about:blank",
            "title": "Validation",
            "status": 422,
            "detail": "bad input",
            "extra": {"field": "format", "reason": "unknown"},
        },
    )
    err = map_response_to_error(resp)
    assert err is not None
    assert err.problem is not None
    assert err.problem.extra == {"field": "format", "reason": "unknown"}


def test_non_problem_response_synthesizes_problem() -> None:
    resp = httpx.Response(
        status_code=502,
        headers={"content-type": "text/html"},
        content=b"<html>nginx error</html>",
    )
    err = map_response_to_error(resp)
    assert isinstance(err, IdpServerError)
    assert err.problem is not None
    assert err.problem.type == "about:blank"
    assert err.problem.status == 502
    assert "nginx" in err.problem.detail


def test_problem_with_garbage_body_falls_back_cleanly() -> None:
    resp = httpx.Response(
        status_code=500,
        headers={"content-type": "application/problem+json"},
        content=b"<<not json>>",
    )
    err = map_response_to_error(resp)
    assert isinstance(err, IdpServerError)
    assert err.problem is not None
    # Garbage problem-json: the synthesized fallback fires.
    assert err.problem.status == 500
