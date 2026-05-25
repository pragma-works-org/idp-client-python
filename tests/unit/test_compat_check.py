"""Tests for ``idp_client.compat`` (parse_semver, normalize, verify)."""

from __future__ import annotations

import pytest

from idp_client.compat import normalize, parse_semver, verify
from idp_client.errors import IdpVersionMismatchError

# ----- parse_semver --------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("0.1.0", (0, 1, 0)),
        ("1.2.3", (1, 2, 3)),
        ("1.2.3-rc.1", (1, 2, 3)),
        ("1.2.3+sha.deadbeef", (1, 2, 3)),
        ("10.20.30", (10, 20, 30)),
    ],
)
def test_parse_semver_happy(raw: str, expected: tuple[int, int, int]) -> None:
    assert parse_semver(raw) == expected


@pytest.mark.parametrize("raw", ["", "1", "1.2", "abc", "v1.2.3"])
def test_parse_semver_rejects_garbage(raw: str) -> None:
    with pytest.raises(ValueError):
        parse_semver(raw)


# ----- normalize -----------------------------------------------------------


def test_normalize_bool_true() -> None:
    assert normalize(True) == "minor"


def test_normalize_bool_false() -> None:
    assert normalize(False) is None


@pytest.mark.parametrize("mode", ["exact", "minor", "major"])
def test_normalize_passthrough(mode: str) -> None:
    assert normalize(mode) == mode  # type: ignore[arg-type]


# ----- verify --------------------------------------------------------------


@pytest.mark.parametrize(
    "server, client_snap, mode, should_pass",
    [
        # exact
        ("0.1.0", "0.1.0", "exact", True),
        ("0.1.1", "0.1.0", "exact", False),
        # minor: same major.minor, server >= snap
        ("0.1.0", "0.1.0", "minor", True),
        ("0.1.5", "0.1.0", "minor", True),
        ("0.2.0", "0.1.0", "minor", False),
        ("0.1.0", "0.1.5", "minor", False),
        # major: same major, server >= snap
        ("0.1.0", "0.1.0", "major", True),
        ("0.5.0", "0.1.0", "major", True),
        ("1.0.0", "0.9.9", "major", False),
        ("0.0.5", "0.1.0", "major", False),
    ],
)
def test_verify_rules(
    server: str,
    client_snap: str,
    mode: str,
    should_pass: bool,
) -> None:
    if should_pass:
        verify(server, client_snap, mode)  # type: ignore[arg-type]
        return
    with pytest.raises(IdpVersionMismatchError):
        verify(server, client_snap, mode)  # type: ignore[arg-type]
