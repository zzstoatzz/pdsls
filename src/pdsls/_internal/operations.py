"""atproto record operations."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if sys.version_info >= (3, 11):
    from datetime import UTC
else:
    UTC = timezone.utc

if TYPE_CHECKING:
    from atproto import AsyncClient, models

from pdsls._internal.types import RecordValue


async def list_records(
    client: AsyncClient,
    collection: str,
    limit: int,
    repo: str | None = None,
) -> list[models.ComAtprotoRepoListRecords.Record]:
    """list records in a collection.

    Args:
        client: authenticated atproto client
        collection: collection name
        limit: maximum number of records
        repo: optional repo DID (defaults to authenticated user)

    Returns:
        list of records
    """
    target_repo = repo or (client.me.did if client.me else None)
    if not target_repo:
        raise ValueError("no repo specified and not authenticated")

    response = await client.com.atproto.repo.list_records(
        {
            "repo": target_repo,
            "collection": collection,
            "limit": limit,
        }
    )

    return response.records


async def get_record(
    client: AsyncClient,
    uri: str,
) -> models.ComAtprotoRepoGetRecord.Response:
    """get a specific record.

    Args:
        client: authenticated atproto client
        uri: record AT-URI

    Returns:
        record response
    """
    parts = uri.replace("at://", "").split("/")
    if len(parts) != 3:
        raise ValueError(f"invalid URI format: {uri}")

    repo, collection, rkey = parts

    return await client.com.atproto.repo.get_record(
        {
            "repo": repo,
            "collection": collection,
            "rkey": rkey,
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
        uri: record AT-URI
        updates: fields to update

    Returns:
        updated record response
    """
    parts = uri.replace("at://", "").split("/")
    if len(parts) != 3:
        raise ValueError(f"invalid URI format: {uri}")

    repo, collection, rkey = parts

    # get current
    current = await client.com.atproto.repo.get_record(
        {
            "repo": repo,
            "collection": collection,
            "rkey": rkey,
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
            "repo": repo,
            "collection": collection,
            "rkey": rkey,
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
        uri: record AT-URI
    """
    parts = uri.replace("at://", "").split("/")
    if len(parts) != 3:
        raise ValueError(f"invalid URI format: {uri}")

    repo, collection, rkey = parts

    await client.com.atproto.repo.delete_record(
        {
            "repo": repo,
            "collection": collection,
            "rkey": rkey,
        }
    )
