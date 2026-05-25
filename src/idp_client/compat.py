"""Opt-in lazy server/client version compatibility check.

The facade calls :func:`verify` after parsing ``HealthResponse.version`` from
the first request when ``compat_check`` is enabled. ``compat.py`` itself is a
pure-function module so each rule is unit-testable in isolation.

K3:A — ``parse_semver`` is inlined here; there is no shared ``_internal.py``.
"""

from __future__ import annotations

import re
from typing import Literal

from .errors import IdpVersionMismatchError

CompatMode = Literal["exact", "minor", "major"] | bool

_SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)")


def parse_semver(s: str) -> tuple[int, int, int]:
    """Return the leading ``(major, minor, patch)`` triple from a semver string.

    Pre-release / build metadata suffixes are tolerated and ignored.
    """
    m = _SEMVER.match(s)
    if not m:
        raise ValueError(f"not a semver: {s!r}")
    return int(m[1]), int(m[2]), int(m[3])


def normalize(mode: CompatMode) -> Literal["exact", "minor", "major"] | None:
    """Collapse the public ``CompatMode`` shape to a string or ``None``.

    ``True`` → ``"minor"``; ``False`` → ``None`` (disabled). Strings pass through.
    """
    if mode is False:
        return None
    if mode is True:
        return "minor"
    return mode


def verify(
    server_version: str,
    client_api_lib_version: str,
    mode: Literal["exact", "minor", "major"],
) -> None:
    """Compare the server's reported version against the committed snapshot.

    Rules:
        ``exact`` — full triple equality.
        ``minor`` — same ``major.minor``; server must be ≥ snapshot.
        ``major`` — same ``major``; server must be ≥ snapshot.

    Raises:
        IdpVersionMismatchError: When the rule fails.
        ValueError: When either string is not a parseable semver.
    """
    s = parse_semver(server_version)
    c = parse_semver(client_api_lib_version)
    if mode == "exact":
        ok = s == c
    elif mode == "minor":
        ok = s[:2] == c[:2] and s >= c
    else:  # "major"
        ok = s[0] == c[0] and s >= c
    if not ok:
        raise IdpVersionMismatchError(
            f"server {server_version} incompatible with client snapshot "
            f"{client_api_lib_version} (mode={mode})"
        )
