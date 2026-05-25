"""Tests for ``idp_client.auth.resolve_api_key``."""

from __future__ import annotations

import pytest

from idp_client.auth import resolve_api_key
from idp_client.errors import IdpAuthError


def test_explicit_param_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IDP_API_KEY", "from-env")
    assert resolve_api_key("from-param") == "from-param"


def test_falls_back_to_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IDP_API_KEY", "from-env")
    assert resolve_api_key(None) == "from-env"


def test_empty_param_falls_through_to_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IDP_API_KEY", "from-env")
    assert resolve_api_key("") == "from-env"


def test_missing_raises() -> None:
    with pytest.raises(IdpAuthError) as excinfo:
        resolve_api_key(None)
    assert "IDP_API_KEY" in str(excinfo.value)
    assert excinfo.value.status == 0
    assert excinfo.value.problem is None
