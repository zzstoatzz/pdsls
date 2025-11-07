"""authentication utilities for atproto."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

if TYPE_CHECKING:
    from atproto import AsyncClient

console = Console()

# silence httpx logs
logging.getLogger("httpx").setLevel(logging.CRITICAL)


async def login(
    client: AsyncClient,
    handle: str | None = None,
    password: str | None = None,
    *,
    silent: bool = False,
) -> None:
    """authenticate with atproto.

    Args:
        client: atproto client to authenticate
        handle: user handle
        password: user password
        silent: suppress authentication output
    """
    if not handle or not password:
        console.print(
            "[red]error:[/red] provide --handle/--password or set ATPROTO_HANDLE/ATPROTO_PASSWORD"
        )
        sys.exit(1)

    if not silent:
        with Progress(
            SpinnerColumn(),
            TextColumn("[dim]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("authenticating...", total=None)
            await client.login(handle, password)
        console.print(f"[dim]✓ authenticated as[/dim] {handle}\n")
    else:
        await client.login(handle, password)
