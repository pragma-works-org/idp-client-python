"""Typer CLI for idp-client.

Console-script entry: ``idp-client`` (registered in ``pyproject.toml``).

Global flags (``--api-key``, ``--base-url``, ``--timeout``, ``--output``) are
declared on the root callback and accessed via the Typer context inside each
command. ``--output`` controls how each command renders its result:

    * ``raw``   — the bare value (default for ``extract`` body output)
    * ``json``  — single-line JSON (machine-readable)
    * ``table`` — pretty rendering for status/list-shaped responses
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Literal

import typer

from ._version import __version__
from .client import IdpClient

OutputFormat = Literal["table", "json", "raw"]


@dataclass
class CliContext:
    api_key: str | None
    base_url: str
    timeout: float
    output: OutputFormat


app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Python client for the ocr-svc IDP REST API.",
)


@app.callback()
def _root(
    ctx: typer.Context,
    api_key: Annotated[
        str | None,
        typer.Option(
            "--api-key",
            envvar="IDP_API_KEY",
            help="Customer API key. Falls back to IDP_API_KEY env.",
        ),
    ] = None,
    base_url: Annotated[
        str,
        typer.Option(
            "--base-url",
            envvar="IDP_BASE_URL",
            help="Base URL of the api-lib service.",
        ),
    ] = "http://localhost:8000",
    timeout: Annotated[
        float,
        typer.Option("--timeout", help="Request timeout, seconds."),
    ] = 30.0,
    output: Annotated[
        str,
        typer.Option(
            "--output",
            "-o",
            help="Output style: table | json | raw.",
            case_sensitive=False,
        ),
    ] = "table",
) -> None:
    output_lower = output.lower()
    if output_lower not in ("table", "json", "raw"):
        raise typer.BadParameter(f"--output must be table|json|raw (got {output!r})")
    ctx.obj = CliContext(
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
        output=output_lower,  # type: ignore[arg-type]
    )


@app.command()
def health(ctx: typer.Context) -> None:
    """Hit ``GET /health/`` and print the server's status. Exits non-zero on failure."""
    cli_ctx: CliContext = ctx.obj
    try:
        with _build_client(cli_ctx) as client:
            response = client.health()
    except Exception as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    rendered = _render_health(response.status, response.version, cli_ctx.output)
    typer.echo(rendered)


@app.command()
def version(ctx: typer.Context) -> None:
    """Print client + snapshot versions; on ``--output json`` emits a JSON object."""
    from . import __api_lib_version__

    cli_ctx: CliContext = ctx.obj
    payload = {
        "client": __version__,
        "api_lib_snapshot": __api_lib_version__,
    }
    if cli_ctx.output == "json":
        typer.echo(json.dumps(payload))
        return
    typer.echo(f"idp-client {__version__} (api-lib snapshot {__api_lib_version__})")


jobs_app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Manage asynchronous extraction jobs.",
)
app.add_typer(jobs_app, name="jobs")


# ----- extract -----------------------------------------------------------


@app.command()
def extract(
    ctx: typer.Context,
    file: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, readable=True, help="Document to extract."),
    ],
    format: Annotated[
        str | None,
        typer.Option("--format", "-f", help="text | markdown | json | doctags."),
    ] = None,
    languages: Annotated[
        str | None,
        typer.Option(
            "--languages",
            "-l",
            help="Comma-separated OCR language hints (e.g. 'en,es').",
        ),
    ] = None,
) -> None:
    """``POST /v1/extraction/sync`` — synchronous extraction; prints the result."""
    cli_ctx: CliContext = ctx.obj
    try:
        with _build_client(cli_ctx) as client:
            response = client.extract(file, format=format, languages=languages)
    except Exception as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(_render_extract_response(response, cli_ctx.output))


# ----- jobs --------------------------------------------------------------


@jobs_app.command("submit")
def jobs_submit(
    ctx: typer.Context,
    file: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, readable=True, help="Document to extract."),
    ],
    format: Annotated[
        str | None,
        typer.Option("--format", "-f", help="text | markdown | json | doctags."),
    ] = None,
    languages: Annotated[
        str | None,
        typer.Option("--languages", "-l", help="Comma-separated OCR language hints."),
    ] = None,
) -> None:
    """``POST /v1/extraction/jobs`` — submit an async job; prints the assigned id."""
    cli_ctx: CliContext = ctx.obj
    try:
        with _build_client(cli_ctx) as client:
            job = client.submit_job(file, format=format, languages=languages)
    except Exception as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(_render_job(job, cli_ctx.output))


@jobs_app.command("status")
def jobs_status(ctx: typer.Context, job_id: str) -> None:
    """``GET /v1/extraction/jobs/{id}`` — print current status."""
    cli_ctx: CliContext = ctx.obj
    try:
        with _build_client(cli_ctx) as client:
            job = client.get_job(job_id)
    except Exception as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(_render_job(job, cli_ctx.output))


@jobs_app.command("result")
def jobs_result(
    ctx: typer.Context,
    job_id: str,
    out: Annotated[
        Path | None,
        typer.Option("--out", "-o", help="Write the body to a file instead of stdout."),
    ] = None,
) -> None:
    """``GET /v1/extraction/jobs/{id}/result`` — fetch the final result."""
    cli_ctx: CliContext = ctx.obj
    try:
        with _build_client(cli_ctx) as client:
            response = client.get_job_result(job_id)
    except Exception as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    rendered = _render_extract_response(response, cli_ctx.output)
    if out is not None:
        out.write_text(rendered, encoding="utf-8")
        typer.echo(f"wrote: {out}")
    else:
        typer.echo(rendered)


@jobs_app.command("cancel")
def jobs_cancel(ctx: typer.Context, job_id: str) -> None:
    """``DELETE /v1/extraction/jobs/{id}`` — cancel a queued or running job."""
    cli_ctx: CliContext = ctx.obj
    try:
        with _build_client(cli_ctx) as client:
            client.cancel_job(job_id)
    except Exception as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"cancelled: {job_id}")


# ----- shared helpers -----------------------------------------------------


def _build_client(cli_ctx: CliContext) -> IdpClient:
    return IdpClient(
        api_key=cli_ctx.api_key,
        base_url=cli_ctx.base_url,
        timeout=cli_ctx.timeout,
    )


def _render_health(status: object, server_version: str, output: OutputFormat) -> str:
    status_str = getattr(status, "value", str(status))
    if output == "json":
        return json.dumps({"status": status_str, "version": server_version})
    if output == "raw":
        return status_str
    # table
    return f"status: {status_str}\nversion: {server_version}"


def _render_extract_response(response: Any, output: OutputFormat) -> str:
    """Render an ``ExtractResponse`` per ``--output``.

    Default for ``extract`` / ``jobs result`` is ``raw`` (joined text per page,
    one blank line between pages) — that's the convenience path the API was
    designed around.
    """
    payload = _to_dict(response)
    if output == "json":
        return json.dumps(payload)
    pages = payload.get("pages") or []
    if output == "table":
        page_count = payload.get("page_count")
        proc = payload.get("processing_time_seconds")
        body = "\n\n".join(str(p) for p in pages)
        return f"page_count: {page_count}\nprocessing_time_seconds: {proc}\n---\n{body}"
    # raw: just the joined page text
    return "\n\n".join(str(p) for p in pages)


def _render_job(job: Any, output: OutputFormat) -> str:
    payload = _to_dict(job)
    if output == "json":
        return json.dumps(payload, default=str)
    if output == "raw":
        return str(payload.get("id", ""))
    rows = [
        ("id", payload.get("id", "")),
        ("status", _enum_value(payload.get("status"))),
        ("created_at", payload.get("created_at", "")),
        ("started_at", payload.get("started_at", "")),
        ("completed_at", payload.get("completed_at", "")),
        ("page_count", payload.get("page_count", "")),
        ("error", payload.get("error", "")),
        ("result_url", payload.get("result_url", "")),
    ]
    width = max(len(k) for k, _ in rows)
    return "\n".join(f"{k:<{width}}  {v}" for k, v in rows if v not in (None, ""))


def _enum_value(value: object) -> object:
    return getattr(value, "value", value)


def _to_dict(obj: Any) -> dict[str, Any]:
    """Coerce an attrs-generated model (or anything with ``to_dict``) into a dict."""
    if isinstance(obj, dict):
        return obj
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        result = to_dict()
        if isinstance(result, dict):
            return result
    raise TypeError(f"Cannot render object of type {type(obj).__name__}")


def main() -> None:  # pragma: no cover - thin wrapper for ``python -m``.
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
