"""Exception hierarchy + RFC 7807 (`application/problem+json`) response mapper.

Public exceptions are all subclasses of :class:`IdpError`. Mapping rules live
in ``_STATUS_MAP``; HTTP responses that don't carry ``application/problem+json``
get a synthesized :class:`ProblemDetails` so callers can treat the field set
uniformly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class ProblemDetails:
    """RFC 7807 problem document. Mirrors api-lib's ``core/errors.ProblemDetails``."""

    type: str
    title: str
    status: int
    detail: str
    extra: dict[str, Any] | None = None


class IdpError(Exception):
    """Base for every client-raised exception."""


class IdpHTTPError(IdpError):
    """Raised when the server returns a non-2xx response."""

    def __init__(
        self,
        *,
        status: int,
        problem: ProblemDetails | None,
        message: str | None = None,
    ) -> None:
        super().__init__(
            message or (problem.detail if problem else f"HTTP {status}"),
        )
        self.status = status
        self.problem = problem


class IdpAuthError(IdpHTTPError):
    """401 / 403 from the server, or a missing API key locally."""


class IdpNotFoundError(IdpHTTPError):
    """404."""


class IdpValidationError(IdpHTTPError):
    """422."""


class IdpServerError(IdpHTTPError):
    """5xx."""


class IdpJobFailed(IdpError):
    """Caller-raised when a polled job lands in a terminal ``failed`` status."""


class IdpVersionMismatchError(IdpError):
    """``compat_check`` enabled and the server's reported version is incompatible."""


_STATUS_MAP: dict[int, type[IdpHTTPError]] = {
    401: IdpAuthError,
    403: IdpAuthError,
    404: IdpNotFoundError,
    422: IdpValidationError,
}


def map_response_to_error(resp: httpx.Response) -> IdpHTTPError | None:
    """Translate a non-success response into a typed exception.

    Returns ``None`` when ``resp`` is 2xx so call sites can write
    ``if err := map_response_to_error(resp): raise err``.
    """
    if resp.is_success:
        return None
    problem = _parse_problem(resp)
    cls: type[IdpHTTPError]
    if resp.status_code in _STATUS_MAP:
        cls = _STATUS_MAP[resp.status_code]
    elif resp.status_code >= 500:
        cls = IdpServerError
    else:
        cls = IdpHTTPError
    return cls(status=resp.status_code, problem=problem)


def _parse_problem(resp: httpx.Response) -> ProblemDetails | None:
    content_type = resp.headers.get("content-type", "")
    if content_type.startswith("application/problem+json"):
        try:
            body = resp.json()
        except ValueError:
            body = {}
        if isinstance(body, dict):
            return ProblemDetails(
                type=str(body.get("type", "about:blank")),
                title=str(body.get("title", "")),
                status=int(body.get("status", resp.status_code)),
                detail=str(body.get("detail", "")),
                extra=_extra_dict(body.get("extra")),
            )
    return ProblemDetails(
        type="about:blank",
        title=resp.reason_phrase or "",
        status=resp.status_code,
        detail=resp.text[:200],
        extra=None,
    )


def _extra_dict(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return {str(k): v for k, v in value.items()}
    return None
