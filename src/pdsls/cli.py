"""general-purpose cli for atproto record operations."""

from __future__ import annotations

import argparse
import asyncio
import sys
import warnings
from typing import NoReturn

# suppress pydantic warnings from atproto library
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

from atproto import AsyncClient  # noqa: E402

from pdsls._internal.auth import login  # noqa: E402
from pdsls._internal.config import settings  # noqa: E402
from pdsls._internal.display import (  # noqa: E402
    console,
    display_record,
    display_records,
    display_success,
)
from pdsls._internal.operations import (  # noqa: E402
    create_record,
    delete_record,
    get_record,
    list_records,
    update_record,
)
from pdsls._internal.output import OutputFormat  # noqa: E402
from pdsls._internal.parsing import parse_key_value_args  # noqa: E402
from pdsls._internal.types import RecordValue  # noqa: E402


async def cmd_list(
    client: AsyncClient,
    collection: str,
    limit: int,
    repo: str | None = None,
    output_format: OutputFormat | None = None,
) -> None:
    """list records in a collection."""
    records = await list_records(client, collection, limit, repo)

    # determine output format - default to compact (most readable for most data)
    fmt = output_format or OutputFormat.COMPACT

    display_records(collection, records, output_format=fmt)


async def cmd_get(client: AsyncClient, uri: str) -> None:
    """get a specific record."""
    response = await get_record(client, uri)
    display_record(response)


async def cmd_create(
    client: AsyncClient,
    collection: str,
    record: dict[str, RecordValue],
) -> None:
    """create a new record."""
    response = await create_record(client, collection, record)
    display_success("created", response.uri, response.cid, collection)


async def cmd_update(
    client: AsyncClient,
    uri: str,
    updates: dict[str, RecordValue],
) -> None:
    """update an existing record."""
    response = await update_record(client, uri, updates)
    display_success("updated", response.uri, response.cid)


async def cmd_delete(client: AsyncClient, uri: str) -> None:
    """delete a record."""
    await delete_record(client, uri)
    display_success("deleted", "", "")


async def async_main() -> int:
    """main entry point."""
    parser = argparse.ArgumentParser(
        description="atproto record operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # version flag
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"pdsls {__import__('pdsls').__version__}",
    )

    # global auth options only
    parser.add_argument("--handle", help="atproto handle")
    parser.add_argument("--password", help="atproto password")
    parser.add_argument("--pds", help="pds url (default: https://bsky.social)")

    subparsers = parser.add_subparsers(dest="command", help="command")

    # list (ls alias)
    list_parser = subparsers.add_parser("list", aliases=["ls"], help="list records")
    list_parser.add_argument(
        "collection", help="collection name (e.g., app.bsky.feed.post)"
    )
    list_parser.add_argument("--repo", help="repo DID (default: authenticated user)")
    list_parser.add_argument("--limit", type=int, default=50, help="max records")
    list_parser.add_argument(
        "-o",
        "--output",
        choices=["json", "yaml", "table", "compact"],
        help="output format (default: compact)",
    )

    # get (cat alias)
    get_parser = subparsers.add_parser("get", aliases=["cat"], help="get record")
    get_parser.add_argument("uri", help="record AT-URI")

    # create (touch/add aliases)
    create_parser = subparsers.add_parser("create", aliases=["touch", "add"], help="create record")
    create_parser.add_argument("collection", help="collection name")
    create_parser.add_argument(
        "fields",
        nargs="+",
        help="record fields as key=value pairs (e.g., title='My Song' artist='Artist')",
    )

    # update (edit alias)
    update_parser = subparsers.add_parser("update", aliases=["edit"], help="update record")
    update_parser.add_argument("uri", help="record AT-URI")
    update_parser.add_argument(
        "fields", nargs="+", help="fields to update as key=value pairs"
    )

    # delete (rm alias)
    delete_parser = subparsers.add_parser("delete", aliases=["rm"], help="delete record")
    delete_parser.add_argument("uri", help="record AT-URI")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # update pds if provided
    if args.pds:
        settings.atproto_pds_url = args.pds

    try:
        client = AsyncClient(base_url=settings.atproto_pds_url)
        await login(
            client,
            args.handle or settings.atproto_handle,
            args.password or settings.atproto_password,
            silent=True,  # always silent by default
        )

        if args.command in ("list", "ls"):
            output_fmt = OutputFormat(args.output) if args.output else None
            await cmd_list(
                client,
                args.collection,
                args.limit,
                args.repo,
                output_format=output_fmt,
            )

        elif args.command in ("get", "cat"):
            await cmd_get(client, args.uri)

        elif args.command in ("create", "touch", "add"):
            record = parse_key_value_args(args.fields)
            await cmd_create(client, args.collection, record)

        elif args.command in ("update", "edit"):
            updates = parse_key_value_args(args.fields)
            await cmd_update(client, args.uri, updates)

        elif args.command in ("delete", "rm"):
            await cmd_delete(client, args.uri)

        return 0

    except Exception as e:
        console.print(f"[red]error:[/red] {e}")
        import os

        if os.getenv("DEBUG"):
            raise
        return 1


def main() -> NoReturn:
    """synchronous entry point."""
    sys.exit(asyncio.run(async_main()))
