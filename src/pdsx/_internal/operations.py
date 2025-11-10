"""atproto record operations."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if sys.version_info >= (3, 11):
    from datetime import UTC
else:
    UTC = timezone.utc

if TYPE_CHECKING:
    from atproto import AsyncClient, models

from pdsx._internal.resolution import URIParts
from pdsx._internal.types import RecordValue


async def list_records(
    client: AsyncClient,
    collection: str,
    limit: int,
    repo: str | None = None,
    cursor: str | None = None,
) -> models.ComAtprotoRepoListRecords.Response:
    """list records in a collection.

    Args:
        client: authenticated atproto client
        collection: collection name
        limit: maximum number of records
        repo: optional repo DID (defaults to authenticated user)
        cursor: optional pagination cursor

    Returns:
        response with records and optional cursor for next page
    """
    target_repo = repo or (client.me.did if client.me else None)
    if not target_repo:
        raise ValueError("no repo specified and not authenticated")

    params: dict[str, str | int] = {
        "repo": target_repo,
        "collection": collection,
        "limit": limit,
    }

    if cursor:
        params["cursor"] = cursor

    return await client.com.atproto.repo.list_records(params)


async def get_record(
    client: AsyncClient,
    uri: str,
) -> models.ComAtprotoRepoGetRecord.Response:
    """get a specific record.

    Args:
        client: authenticated atproto client
        uri: record AT-URI (can be shorthand like 'collection/rkey' if authenticated)

    Returns:
        record response
    """
    parts = URIParts.from_uri(uri, client.me.did if client.me else None)

    return await client.com.atproto.repo.get_record(
        {
            "repo": parts.repo,
            "collection": parts.collection,
            "rkey": parts.rkey,
        }
    )


async def create_record(
    client: AsyncClient,
    collection: str,
    record: dict[str, RecordValue],
) -> models.ComAtprotoRepoCreateRecord.Response:
    """create a new record.

    Args:
        client: authenticated atproto client
        collection: collection name
        record: record data

    Returns:
        created record response
    """
    if client.me is None:
        raise ValueError("not authenticated")

    # ensure $type is set
    if "$type" not in record:
        record["$type"] = collection

    # add createdAt if not present
    if "createdAt" not in record:
        record["createdAt"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    return await client.com.atproto.repo.create_record(
        {
            "repo": client.me.did,
            "collection": collection,
            "record": record,
        }
    )


async def update_record(
    client: AsyncClient,
    uri: str,
    updates: dict[str, RecordValue],
) -> models.ComAtprotoRepoPutRecord.Response:
    """update an existing record.

    Args:
        client: authenticated atproto client
        uri: record AT-URI (can be shorthand like 'collection/rkey' if authenticated)
        updates: fields to update

    Returns:
        updated record response
    """
    parts = URIParts.from_uri(uri, client.me.did if client.me else None)

    # get current
    current = await client.com.atproto.repo.get_record(
        {
            "repo": parts.repo,
            "collection": parts.collection,
            "rkey": parts.rkey,
        }
    )

    # merge
    if isinstance(current.value, dict):
        updated_value = {**current.value, **updates}
    else:
        updated_value = dict(current.value)
        updated_value.update(updates)

    # put
    return await client.com.atproto.repo.put_record(
        {
            "repo": parts.repo,
            "collection": parts.collection,
            "rkey": parts.rkey,
            "record": updated_value,
        }
    )


async def delete_record(
    client: AsyncClient,
    uri: str,
) -> None:
    """delete a record.

    Args:
        client: authenticated atproto client
        uri: record AT-URI (can be shorthand like 'collection/rkey' if authenticated)
    """
    parts = URIParts.from_uri(uri, client.me.did if client.me else None)

    await client.com.atproto.repo.delete_record(
        {
            "repo": parts.repo,
            "collection": parts.collection,
            "rkey": parts.rkey,
        }
    )


async def upload_blob(
    client: AsyncClient,
    file_path: str | Path,
) -> models.ComAtprotoRepoUploadBlob.Response:
    """upload a blob (image, video, etc.).

    Args:
        client: authenticated atproto client
        file_path: path to file to upload

    Returns:
        upload response with blob reference
    """
    if client.me is None:
        raise ValueError("not authenticated")

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"file not found: {file_path}")

    # read file bytes
    data = file_path.read_bytes()

    # upload blob
    return await client.com.atproto.repo.upload_blob(data)
