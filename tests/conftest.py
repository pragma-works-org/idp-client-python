"""Shared fixtures for the idp-client unit suite."""

from __future__ import annotations

from collections.abc import Iterator

import pytest


@pytest.fixture
def api_key() -> str:
    return "test-key-abc123"


@pytest.fixture
def base_url() -> str:
    return "http://api.test.local"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Clear ``IDP_API_KEY`` for every test so env leakage doesn't masquerade as auth."""
    monkeypatch.delenv("IDP_API_KEY", raising=False)
    monkeypatch.delenv("IDP_BASE_URL", raising=False)
    yield


# ----- pytest collection: every test is `unit` unless explicitly marked --


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Attach the ``unit`` marker to anything under ``tests/unit/``.

    Keeps test files free of redundant ``@pytest.mark.unit`` decorators while
    still respecting the ``-m unit`` default in ``pyproject.toml``.
    """
    unit_marker = pytest.mark.unit
    for item in items:
        if "tests/unit/" in str(item.fspath).replace("\\", "/"):
            item.add_marker(unit_marker)
