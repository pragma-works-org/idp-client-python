"""Hand-authored response model for ``POST /v1/embeddings``.

The OpenAPI snapshot declares the 200 response schema as ``{}`` (the server
emits an OpenAI-compatible envelope but does not formalize it in the spec), so
``openapi-python-client`` cannot generate a typed class. We stay attrs-typed to
match the convention used by the rest of the public surface.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from attrs import define, field


@define
class EmbeddingObject:
    """One entry in ``EmbeddingResponse.data``.

    Mirrors OpenAI's ``Embedding`` object: ``index`` is the per-input position,
    ``embedding`` is the vector when ``encoding_format='float'`` and a base64
    string when ``encoding_format='base64'``.
    """

    index: int
    embedding: list[float] | str
    object_: str = "embedding"

    @classmethod
    def from_dict(cls, src: Mapping[str, Any]) -> EmbeddingObject:
        return cls(
            index=int(src["index"]),
            embedding=src["embedding"],
            object_=str(src.get("object", "embedding")),
        )


@define
class EmbeddingUsage:
    """OpenAI's ``usage`` envelope. Both fields default to 0 in case the server
    omits them — the spec does not require them and the surface should not
    raise on a benign omission.
    """

    prompt_tokens: int = 0
    total_tokens: int = 0

    @classmethod
    def from_dict(cls, src: Mapping[str, Any] | None) -> EmbeddingUsage:
        if not src:
            return cls()
        return cls(
            prompt_tokens=int(src.get("prompt_tokens", 0)),
            total_tokens=int(src.get("total_tokens", 0)),
        )


@define
class EmbeddingResponse:
    """Typed wrapper around the OpenAI-compatible ``POST /v1/embeddings`` body.

    Constructed via :meth:`from_dict`. The ``data`` list is in request order
    (so callers can pair each entry with the input string they sent).
    """

    data: list[EmbeddingObject] = field(factory=list)
    model: str = ""
    object_: str = "list"
    usage: EmbeddingUsage = field(factory=EmbeddingUsage)

    @classmethod
    def from_dict(cls, src: Mapping[str, Any]) -> EmbeddingResponse:
        data_raw = src.get("data") or []
        return cls(
            data=[EmbeddingObject.from_dict(item) for item in data_raw],
            model=str(src.get("model", "")),
            object_=str(src.get("object", "list")),
            usage=EmbeddingUsage.from_dict(src.get("usage")),
        )
