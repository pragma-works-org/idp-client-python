"""Tests for ``IdpClient.embed`` (synchronous OpenAI-compatible embedding)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from idp_client import EmbeddingResponse, IdpClient
from idp_client.errors import IdpServerError, IdpValidationError


def _ok_embed_response(dim: int = 4) -> dict[str, object]:
    vec = [0.1] * dim
    return {
        "object": "list",
        "data": [{"index": 0, "object": "embedding", "embedding": vec}],
        "model": "test-profile",
        "usage": {"prompt_tokens": 7, "total_tokens": 7},
    }


def test_embed_happy_path_string_input(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        route = router.post("/v1/embeddings").mock(
            return_value=httpx.Response(200, json=_ok_embed_response(8)),
        )
        with IdpClient(api_key=api_key, base_url=base_url) as client:
            response = client.embed("hello world", model="test-profile")
    assert isinstance(response, EmbeddingResponse)
    assert response.model == "test-profile"
    assert len(response.data) == 1
    assert len(response.data[0].embedding) == 8
    sent = route.calls.last.request
    assert sent.headers["authorization"] == f"Bearer {api_key}"
    assert sent.headers["content-type"] == "application/json"
    body = json.loads(sent.content)
    assert body["model"] == "test-profile"
    assert body["input"] == "hello world"


def test_embed_happy_path_list_input(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        route = router.post("/v1/embeddings").mock(
            return_value=httpx.Response(200, json=_ok_embed_response()),
        )
        with IdpClient(api_key=api_key, base_url=base_url) as client:
            client.embed(["a", "b", "c"], model="test-profile")
    body = json.loads(route.calls.last.request.content)
    assert body["input"] == ["a", "b", "c"]


def test_embed_omits_default_optional_fields(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        route = router.post("/v1/embeddings").mock(
            return_value=httpx.Response(200, json=_ok_embed_response()),
        )
        with IdpClient(api_key=api_key, base_url=base_url) as client:
            client.embed("hi", model="test-profile")
    body = json.loads(route.calls.last.request.content)
    # dimensions left at default (None) must not appear on the wire.
    assert "dimensions" not in body
    # encoding_format defaults to "float" — the generator emits it as a
    # literal "float" string when set. We don't strip it here because the
    # server accepts the explicit default and it documents intent.
    assert body.get("encoding_format", "float") == "float"


def test_embed_explicit_optional_fields_present(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        route = router.post("/v1/embeddings").mock(
            return_value=httpx.Response(200, json=_ok_embed_response()),
        )
        with IdpClient(api_key=api_key, base_url=base_url) as client:
            client.embed(
                "hi",
                model="test-profile",
                dimensions=256,
                encoding_format="base64",
            )
    body = json.loads(route.calls.last.request.content)
    assert body["dimensions"] == 256
    assert body["encoding_format"] == "base64"


def test_embed_422_raises_validation_error(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        router.post("/v1/embeddings").mock(
            return_value=httpx.Response(
                422,
                headers={"content-type": "application/problem+json"},
                content=json.dumps(
                    {
                        "type": "https://errors.idp/validation",
                        "title": "Validation",
                        "status": 422,
                        "detail": "unknown model",
                    },
                ).encode(),
            ),
        )
        with IdpClient(api_key=api_key, base_url=base_url) as client:
            with pytest.raises(IdpValidationError):
                client.embed("hi", model="not-a-real-profile")


def test_embed_5xx_raises_server_error(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        router.post("/v1/embeddings").mock(
            return_value=httpx.Response(503, content=b"down"),
        )
        with IdpClient(api_key=api_key, base_url=base_url) as client:
            with pytest.raises(IdpServerError):
                client.embed("hi", model="test-profile")


def test_embed_response_has_usage(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        router.post("/v1/embeddings").mock(
            return_value=httpx.Response(200, json=_ok_embed_response()),
        )
        with IdpClient(api_key=api_key, base_url=base_url) as client:
            response = client.embed("hello", model="test-profile")
    assert response.usage.prompt_tokens == 7
    assert response.usage.total_tokens == 7
