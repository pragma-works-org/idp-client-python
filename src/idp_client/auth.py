"""API-key resolution. Order: explicit param > ``IDP_API_KEY`` env > raise."""

from __future__ import annotations

import os

from .errors import IdpAuthError

_ENV_VAR = "IDP_API_KEY"


def resolve_api_key(api_key: str | None) -> str:
    """Return the API key to send as ``X-Api-Key`` on every request.

    Raises:
        IdpAuthError: If neither ``api_key`` nor ``IDP_API_KEY`` resolves to
            a non-empty string.
    """
    if api_key:
        return api_key
    env = os.environ.get(_ENV_VAR)
    if env:
        return env
    raise IdpAuthError(
        status=0,
        problem=None,
        message=f"No API key supplied. Pass api_key=... or set {_ENV_VAR}.",
    )
