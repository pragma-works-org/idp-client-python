from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.extract_response import ExtractResponse
from ...models.extract_sync_body import ExtractSyncBody
from ...models.problem_details import ProblemDetails
from ...types import Response


def _get_kwargs(
    *,
    body: ExtractSyncBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/extraction/sync",
    }

    _kwargs["files"] = body.to_multipart()

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ExtractResponse | ProblemDetails | None:
    if response.status_code == 200:
        response_200 = ExtractResponse.from_dict(response.json())

        return response_200

    if response.status_code == 413:
        response_413 = ProblemDetails.from_dict(response.json())

        return response_413

    if response.status_code == 415:
        response_415 = ProblemDetails.from_dict(response.json())

        return response_415

    if response.status_code == 422:
        response_422 = ProblemDetails.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ExtractResponse | ProblemDetails]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ExtractSyncBody,
) -> Response[ExtractResponse | ProblemDetails]:
    """Synchronous extraction (small documents).

    Args:
        body (ExtractSyncBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ExtractResponse | ProblemDetails]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: ExtractSyncBody,
) -> ExtractResponse | ProblemDetails | None:
    """Synchronous extraction (small documents).

    Args:
        body (ExtractSyncBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ExtractResponse | ProblemDetails
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ExtractSyncBody,
) -> Response[ExtractResponse | ProblemDetails]:
    """Synchronous extraction (small documents).

    Args:
        body (ExtractSyncBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ExtractResponse | ProblemDetails]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: ExtractSyncBody,
) -> ExtractResponse | ProblemDetails | None:
    """Synchronous extraction (small documents).

    Args:
        body (ExtractSyncBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ExtractResponse | ProblemDetails
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
