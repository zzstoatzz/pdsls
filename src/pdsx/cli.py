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

from pdsx import __version__  # noqa: E402
from pdsx._internal.auth import login  # noqa: E402
from pdsx._internal.config import settings  # noqa: E402
from pdsx._internal.display import (  # noqa: E402
    console,
    display_record,
    display_records,
    display_success,
)
from pdsx._internal.operations import (  # noqa: E402
    create_record,
    delete_record,
    get_record,
    list_records,
    update_record,
    upload_blob,
)
from pdsx._internal.output import OutputFormat  # noqa: E402
from pdsx._internal.parsing import parse_key_value_args  # noqa: E402
from pdsx._internal.types import RecordValue  # noqa: E402


async def cmd_list(
    client: AsyncClient,
    collection: str,
    limit: int,
    repo: str | None = None,
    cursor: str | None = None,
    output_format: OutputFormat | None = None,
) -> None:
    """list records in a collection."""
    response = await list_records(client, collection, limit, repo, cursor)

    # determine output format - default to compact (most readable for most data)
    fmt = output_format or OutputFormat.COMPACT

    display_records(collection, response.records, output_format=fmt)

    # display cursor if there are more pages
    # for structured output formats (json/yaml), send to stderr to avoid breaking parsing
    if response.cursor:
        structured_formats = (OutputFormat.JSON, OutputFormat.YAML)
        if fmt in structured_formats:
            # use stderr for structured formats to avoid breaking json/yaml parsing
            print(f"\nnext page cursor: {response.cursor}", file=sys.stderr)
        else:
            console.print(f"\n[dim]next page cursor:[/dim] {response.cursor}")


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


async def cmd_upload_blob(client: AsyncClient, file_path: str) -> None:
    """upload a blob (image, video, etc.)."""
    response = await upload_blob(client, file_path)

    # display blob reference in json format for easy copying
    import json

    blob_ref = {
        "$type": "blob",
        "ref": {"$link": response.blob.ref.link},
        "mimeType": response.blob.mime_type,
        "size": response.blob.size,
    }
    console.print("[green]✓[/green] blob uploaded successfully")
    console.print("\n[bold]blob reference:[/bold]")
    console.print(json.dumps(blob_ref, indent=2))
    console.print(
        "\n[dim]use this blob reference in records (e.g., for post embeds)[/dim]"
    )


async def async_main() -> int:
    """main entry point."""
    parser = argparse.ArgumentParser(
        description="atproto record operations",
        epilog="""
examples:
  # read anyone's posts (no auth needed)
  pdsx -r zzstoatzz.io ls app.bsky.feed.post

  # read with DID (more durable than handle)
  pdsx -r did:plc:abc123 ls app.bsky.feed.post

  # list your own records (requires auth)
  pdsx --handle you.bsky.social --password xxxx-xxxx ls app.bsky.feed.post

  # create a record (requires auth)
  pdsx --handle you.bsky.social create app.bsky.feed.post text='hello'

note: -r flag goes BEFORE the command (ls, get, etc.)
      auth flags (--handle, --password) also go BEFORE the command
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # version flag
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"pdsx {__version__}",
    )

    # global identity flag - can be handle or DID
    parser.add_argument(
        "-r",
        "--repo",
        metavar="REPO",
        help="read from another repo (handle or DID) - no auth needed for public data",
    )

    # auth options (only needed for writes to your own repo)
    parser.add_argument(
        "--handle",
        help="your atproto handle for authentication (required for writes)",
    )
    parser.add_argument(
        "--password",
        help="your atproto app password (get from Bluesky settings)",
    )
    parser.add_argument(
        "--pds",
        help="custom PDS URL (auto-discovered from handle if not specified)",
    )

    subparsers = parser.add_subparsers(dest="command", help="command")

    # list (ls alias)
    list_parser = subparsers.add_parser("list", aliases=["ls"], help="list records")
    list_parser.add_argument(
        "collection", help="collection name (e.g., app.bsky.feed.post)"
    )
    list_parser.add_argument("--limit", type=int, default=50, help="max records")
    list_parser.add_argument(
        "--cursor",
        help="pagination cursor from previous response",
    )
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
    create_parser = subparsers.add_parser(
        "create", aliases=["touch", "add"], help="create record"
    )
    create_parser.add_argument("collection", help="collection name")
    create_parser.add_argument(
        "fields",
        nargs="+",
        help="record fields as key=value pairs (e.g., title='My Song' artist='Artist')",
    )

    # update (edit alias)
    update_parser = subparsers.add_parser(
        "update", aliases=["edit"], help="update record"
    )
    update_parser.add_argument("uri", help="record AT-URI")
    update_parser.add_argument(
        "fields", nargs="+", help="fields to update as key=value pairs"
    )

    # delete (rm alias)
    delete_parser = subparsers.add_parser(
        "delete", aliases=["rm"], help="delete record"
    )
    delete_parser.add_argument("uri", help="record AT-URI")

    # upload-blob
    upload_blob_parser = subparsers.add_parser(
        "upload-blob", help="upload a blob (image, video, etc.)"
    )
    upload_blob_parser.add_argument("file_path", help="path to file to upload")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # update pds if provided
    if args.pds:
        settings.atproto_pds_url = args.pds

    try:
        # determine if auth is needed
        # reads with --repo don't need auth, writes always need auth
        read_commands = ("list", "ls", "get", "cat")
        is_read = args.command in read_commands
        has_repo_target = args.repo is not None

        # auth required if: doing a write operation OR doing a read without --repo
        auth_needed = not is_read or not has_repo_target

        # create client with or without base_url depending on auth
        if auth_needed:
            # for authenticated operations, let SDK discover PDS from handle
            # unless user explicitly provided --pds flag
            if args.pds:
                client = AsyncClient(base_url=args.pds)
            else:
                client = AsyncClient()  # will discover PDS during login

            await login(
                client,
                args.handle or settings.atproto_handle,
                args.password or settings.atproto_password,
                silent=True,
                required=True,
            )
        else:
            # for unauthenticated reads with -r, use default or provided PDS
            client = AsyncClient(base_url=settings.atproto_pds_url)

        if args.command in ("list", "ls"):
            output_fmt = OutputFormat(args.output) if args.output else None
            await cmd_list(
                client,
                args.collection,
                args.limit,
                args.repo,
                args.cursor,
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

        elif args.command == "upload-blob":
            await cmd_upload_blob(client, args.file_path)

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
