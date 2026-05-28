"""Public API for the ocr-svc IDP Python client.

Re-exports the sync facade, exception hierarchy, and version constants. The
``AsyncIdpClient`` re-export is added in Phase 3.
"""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

from ._version import __version__


def _read_api_lib_version() -> str:
    """Read ``info.version`` out of the committed ``openapi/openapi.json``.

    The snapshot ships *next to* the package (under ``service-clients/idp-client/openapi/``)
    rather than inside it, so ``importlib.resources`` cannot find it once
    installed. We walk a few candidate locations: the editable-install
    location, then the installed-package location (where the file would have
    been bundled into the wheel via ``[tool.hatch.build]`` or similar). If
    nothing is found, fall back to a string the snapshot was authored to
    expose so import never raises.
    """
    candidates: list[Path] = []
    here = Path(__file__).resolve()
    # Editable install: src/idp_client/__init__.py → ../../openapi/openapi.json
    candidates.append(here.parent.parent.parent / "openapi" / "openapi.json")
    # Bundled install: src/idp_client/__init__.py → ./openapi/openapi.json
    candidates.append(here.parent / "openapi" / "openapi.json")
    # importlib.resources (when bundled into the wheel as package data)
    try:
        with resources.as_file(resources.files("idp_client") / "openapi" / "openapi.json") as p:
            candidates.append(p)
    except (FileNotFoundError, ModuleNotFoundError, AttributeError):
        pass

    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, ValueError):
            continue
        version = data.get("info", {}).get("version")
        if isinstance(version, str) and version:
            return version
    return "0.0.0"


__api_lib_version__: str = _read_api_lib_version()


from .async_client import AsyncIdpClient  # noqa: E402
from .client import IdpClient  # noqa: E402  (after __api_lib_version__ for client import)
from .embedding import EmbeddingObject, EmbeddingResponse, EmbeddingUsage  # noqa: E402
from .errors import (  # noqa: E402
    IdpAuthError,
    IdpError,
    IdpHTTPError,
    IdpJobFailed,
    IdpNotFoundError,
    IdpServerError,
    IdpValidationError,
    IdpVersionMismatchError,
    ProblemDetails,
)

__all__ = (
    "IdpClient",
    "AsyncIdpClient",
    "EmbeddingResponse",
    "EmbeddingObject",
    "EmbeddingUsage",
    "IdpError",
    "IdpHTTPError",
    "IdpAuthError",
    "IdpNotFoundError",
    "IdpValidationError",
    "IdpServerError",
    "IdpJobFailed",
    "IdpVersionMismatchError",
    "ProblemDetails",
    "__api_lib_version__",
    "__version__",
)
