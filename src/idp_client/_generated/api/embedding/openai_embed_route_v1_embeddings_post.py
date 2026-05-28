from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.open_ai_embedding_request import OpenAIEmbeddingRequest
from ...types import Response


def _get_kwargs(
    *,
    body: OpenAIEmbeddingRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/embeddings",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | None:
    if response.status_code == 200:
        return None

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: OpenAIEmbeddingRequest,
) -> Response[Any]:
    r"""Openai Embed Route

     OpenAI-compatible embeddings endpoint.

    Emits OpenAI's error envelope (`{\"error\": {...}}`) instead of RFC 7807 by
    catching `DomainError` locally. The native `EmbeddingService` is the
    canonical core — we adapt input/output shapes only.

    Args:
        body (OpenAIEmbeddingRequest): OpenAI's `POST /v1/embeddings` request shape.

            `input` accepts string, list[str], list[int], list[list[int]] per the spec.
            Pre-tokenized inputs (the int variants) are rejected with 400 in v1 (Q5:A).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: OpenAIEmbeddingRequest,
) -> Response[Any]:
    r"""Openai Embed Route

     OpenAI-compatible embeddings endpoint.

    Emits OpenAI's error envelope (`{\"error\": {...}}`) instead of RFC 7807 by
    catching `DomainError` locally. The native `EmbeddingService` is the
    canonical core — we adapt input/output shapes only.

    Args:
        body (OpenAIEmbeddingRequest): OpenAI's `POST /v1/embeddings` request shape.

            `input` accepts string, list[str], list[int], list[list[int]] per the spec.
            Pre-tokenized inputs (the int variants) are rejected with 400 in v1 (Q5:A).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
