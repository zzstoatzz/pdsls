"""batch operations for concurrent CRUD operations."""

import asyncio
import sys
from dataclasses import dataclass

from atproto import AsyncClient
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
)

from pdsx._internal.display import console
from pdsx._internal.operations import create_record, delete_record
from pdsx._internal.types import RecordValue


@dataclass
class BatchResult:
    """result of a batch operation."""

    successful: list[str]
    failed: list[tuple[str, Exception]]

    @property
    def total(self) -> int:
        """total operations attempted."""
        return len(self.successful) + len(self.failed)

    @property
    def success_rate(self) -> float:
        """success rate as percentage."""
        return len(self.successful) / self.total * 100 if self.total > 0 else 0


async def batch_delete(
    client: AsyncClient,
    uris: list[str],
    *,
    concurrency: int = 10,
    fail_fast: bool = False,
    show_progress: bool = True,
) -> BatchResult:
    """delete multiple records concurrently.

    Args:
        client: authenticated atproto client
        uris: list of record URIs to delete
        concurrency: maximum concurrent operations (default: 10)
        fail_fast: stop on first error (default: False)
        show_progress: show progress bar (default: True)

    Returns:
        batch result with successful and failed operations
    """
    successful: list[str] = []
    failed: list[tuple[str, Exception]] = []
    semaphore = asyncio.Semaphore(concurrency)

    progress: Progress | None = None
    task_id: TaskID | None = None

    if show_progress:
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            console=console,
        )
        progress.start()
        task_id = progress.add_task("deleting records", total=len(uris))

    async def delete_one(uri: str) -> None:
        """delete a single record with concurrency control."""
        async with semaphore:
            try:
                await delete_record(client, uri)
                successful.append(uri)
            except Exception as e:
                failed.append((uri, e))
                if fail_fast:
                    raise
            finally:
                if progress and task_id is not None:
                    progress.update(task_id, advance=1)

    try:
        await asyncio.gather(*[delete_one(uri) for uri in uris])
    except Exception:
        # fail_fast raised an exception
        pass
    finally:
        if progress:
            progress.stop()

    return BatchResult(successful=successful, failed=failed)


async def batch_create(
    client: AsyncClient,
    collection: str,
    records: list[dict[str, RecordValue]],
    *,
    concurrency: int = 10,
    fail_fast: bool = False,
    show_progress: bool = True,
) -> BatchResult:
    """create multiple records concurrently.

    Args:
        client: authenticated atproto client
        collection: collection name
        records: list of record data dictionaries
        concurrency: maximum concurrent operations (default: 10)
        fail_fast: stop on first error (default: False)
        show_progress: show progress bar (default: True)

    Returns:
        batch result with successful URIs and failed operations
    """
    successful: list[str] = []
    failed: list[tuple[str, Exception]] = []
    semaphore = asyncio.Semaphore(concurrency)

    progress: Progress | None = None
    task_id: TaskID | None = None

    if show_progress:
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            console=console,
        )
        progress.start()
        task_id = progress.add_task("creating records", total=len(records))

    async def create_one(record: dict[str, RecordValue], index: int) -> None:
        """create a single record with concurrency control."""
        async with semaphore:
            try:
                response = await create_record(client, collection, record)
                successful.append(response.uri)
            except Exception as e:
                # use index as identifier since we don't have URI yet
                failed.append((f"record #{index + 1}", e))
                if fail_fast:
                    raise
            finally:
                if progress and task_id is not None:
                    progress.update(task_id, advance=1)

    try:
        await asyncio.gather(
            *[create_one(record, i) for i, record in enumerate(records)]
        )
    except Exception:
        # fail_fast raised an exception
        pass
    finally:
        if progress:
            progress.stop()

    return BatchResult(successful=successful, failed=failed)


def read_uris_from_stdin() -> list[str]:
    """read URIs from stdin, one per line.

    Returns:
        list of URIs read from stdin
    """
    if sys.stdin.isatty():
        return []

    return [line.strip() for line in sys.stdin if line.strip()]


def read_records_from_stdin() -> list[dict[str, RecordValue]]:
    """read JSONL records from stdin, one JSON object per line.

    Returns:
        list of record dictionaries parsed from JSONL

    Raises:
        ValueError: if JSON parsing fails
    """
    import json

    if sys.stdin.isatty():
        return []

    records = []
    for line_num, line in enumerate(sys.stdin, start=1):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(
                    f"line {line_num}: expected JSON object, got {type(record).__name__}"
                )
            records.append(record)
        except json.JSONDecodeError as e:
            raise ValueError(f"line {line_num}: invalid JSON - {e}") from e

    return records


def display_batch_result(result: BatchResult, operation: str = "deleted") -> None:
    """display batch operation results.

    Args:
        result: batch operation result
        operation: operation name for display (e.g., "deleted", "updated")
    """
    if result.successful:
        console.print(
            f"[green]✓[/green] successfully {operation} {len(result.successful)}/{result.total} records "
            f"({result.success_rate:.0f}%)"
        )

    if result.failed:
        console.print(f"\n[red]✗[/red] {len(result.failed)} operations failed:")
        for uri, error in result.failed[:10]:  # show first 10 errors
            # extract rkey from URI for compact display
            rkey = uri.split("/")[-1]
            error_msg = str(error).split("\n")[0]  # first line only
            console.print(f"  [dim]{rkey}:[/dim] {error_msg}")

        if len(result.failed) > 10:
            console.print(f"  [dim]... and {len(result.failed) - 10} more[/dim]")
