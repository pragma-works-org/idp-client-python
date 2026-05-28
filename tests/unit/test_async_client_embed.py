"""Async parity tests for ``AsyncIdpClient.embed``."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from idp_client import AsyncIdpClient, EmbeddingResponse
from idp_client.errors import IdpServerError, IdpValidationError


def _ok_embed_response(dim: int = 4) -> dict[str, object]:
    vec = [0.1] * dim
    return {
        "object": "list",
        "data": [{"index": 0, "object": "embedding", "embedding": vec}],
        "model": "test-profile",
        "usage": {"prompt_tokens": 3, "total_tokens": 3},
    }


async def test_async_embed_happy_path_string_input(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        route = router.post("/v1/embeddings").mock(
            return_value=httpx.Response(200, json=_ok_embed_response(8)),
        )
        async with AsyncIdpClient(api_key=api_key, base_url=base_url) as client:
            response = await client.embed("hello world", model="test-profile")
    assert isinstance(response, EmbeddingResponse)
    assert response.model == "test-profile"
    assert len(response.data[0].embedding) == 8
    sent = route.calls.last.request
    assert sent.headers["authorization"] == f"Bearer {api_key}"
    body = json.loads(sent.content)
    assert body == {"model": "test-profile", "input": "hello world", "encoding_format": "float"}


async def test_async_embed_list_input(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        route = router.post("/v1/embeddings").mock(
            return_value=httpx.Response(200, json=_ok_embed_response()),
        )
        async with AsyncIdpClient(api_key=api_key, base_url=base_url) as client:
            await client.embed(["a", "b"], model="test-profile")
    body = json.loads(route.calls.last.request.content)
    assert body["input"] == ["a", "b"]


async def test_async_embed_omits_default_dimensions(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        route = router.post("/v1/embeddings").mock(
            return_value=httpx.Response(200, json=_ok_embed_response()),
        )
        async with AsyncIdpClient(api_key=api_key, base_url=base_url) as client:
            await client.embed("hi", model="test-profile")
    body = json.loads(route.calls.last.request.content)
    assert "dimensions" not in body


async def test_async_embed_explicit_optional_fields(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        route = router.post("/v1/embeddings").mock(
            return_value=httpx.Response(200, json=_ok_embed_response()),
        )
        async with AsyncIdpClient(api_key=api_key, base_url=base_url) as client:
            await client.embed(
                "hi",
                model="test-profile",
                dimensions=512,
                encoding_format="base64",
            )
    body = json.loads(route.calls.last.request.content)
    assert body["dimensions"] == 512
    assert body["encoding_format"] == "base64"


async def test_async_embed_422_raises_validation_error(api_key: str, base_url: str) -> None:
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
        async with AsyncIdpClient(api_key=api_key, base_url=base_url) as client:
            with pytest.raises(IdpValidationError):
                await client.embed("hi", model="not-a-real-profile")


async def test_async_embed_5xx_raises_server_error(api_key: str, base_url: str) -> None:
    with respx.mock(base_url=base_url) as router:
        router.post("/v1/embeddings").mock(
            return_value=httpx.Response(503, content=b"down"),
        )
        async with AsyncIdpClient(api_key=api_key, base_url=base_url) as client:
            with pytest.raises(IdpServerError):
                await client.embed("hi", model="test-profile")
