"""tests for batch operations module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from atproto import AsyncClient

from pdsx._internal.batch import BatchResult, batch_delete, read_uris_from_stdin


@pytest.fixture
def mock_client() -> AsyncClient:
    """create a mock atproto client."""
    client = MagicMock()
    client.me = MagicMock()
    client.me.did = "did:plc:test123"
    return client


class TestBatchDelete:
    """tests for batch_delete function."""

    async def test_batch_delete_all_successful(self, mock_client: AsyncClient) -> None:
        """test batch delete with all operations successful."""
        uris = [
            "at://did:plc:test123/app.bsky.feed.post/abc123",
            "at://did:plc:test123/app.bsky.feed.post/def456",
            "at://did:plc:test123/app.bsky.feed.post/ghi789",
        ]

        with patch("pdsx._internal.batch.delete_record", new_callable=AsyncMock):
            result = await batch_delete(
                mock_client,
                uris,
                show_progress=False,
            )

        assert len(result.successful) == 3
        assert len(result.failed) == 0
        assert result.total == 3
        assert result.success_rate == 100.0

    async def test_batch_delete_with_failures(self, mock_client: AsyncClient) -> None:
        """test batch delete with some failures."""
        uris = [
            "at://did:plc:test123/app.bsky.feed.post/abc123",
            "at://did:plc:test123/app.bsky.feed.post/def456",
            "at://did:plc:test123/app.bsky.feed.post/ghi789",
        ]

        async def mock_delete(client: AsyncClient, uri: str) -> None:
            """mock delete that fails on second URI."""
            if "def456" in uri:
                raise ValueError("simulated failure")

        with patch("pdsx._internal.batch.delete_record", side_effect=mock_delete):
            result = await batch_delete(
                mock_client,
                uris,
                show_progress=False,
            )

        assert len(result.successful) == 2
        assert len(result.failed) == 1
        assert result.total == 3
        assert result.success_rate == pytest.approx(66.67, rel=0.01)
        assert result.failed[0][0] == "at://did:plc:test123/app.bsky.feed.post/def456"
        assert isinstance(result.failed[0][1], ValueError)

    async def test_batch_delete_fail_fast(self, mock_client: AsyncClient) -> None:
        """test batch delete with fail_fast mode."""
        uris = [
            "at://did:plc:test123/app.bsky.feed.post/abc123",
            "at://did:plc:test123/app.bsky.feed.post/def456",
            "at://did:plc:test123/app.bsky.feed.post/ghi789",
        ]

        async def mock_delete(client: AsyncClient, uri: str) -> None:
            """mock delete that fails on second URI."""
            if "def456" in uri:
                raise ValueError("simulated failure")

        with patch("pdsx._internal.batch.delete_record", side_effect=mock_delete):
            result = await batch_delete(
                mock_client,
                uris,
                fail_fast=True,
                show_progress=False,
            )

        # with fail_fast, some operations may not complete
        assert len(result.failed) >= 1
        assert result.total <= 3

    async def test_batch_delete_with_concurrency_limit(
        self, mock_client: AsyncClient
    ) -> None:
        """test batch delete respects concurrency limit."""
        import asyncio

        uris = [f"at://did:plc:test123/app.bsky.feed.post/uri{i}" for i in range(20)]

        max_concurrent = 0
        current_concurrent = 0

        async def mock_delete(client: AsyncClient, uri: str) -> None:
            """mock delete that tracks concurrency."""
            nonlocal max_concurrent, current_concurrent
            current_concurrent += 1
            max_concurrent = max(max_concurrent, current_concurrent)
            await asyncio.sleep(0.01)  # simulate work
            current_concurrent -= 1

        with patch("pdsx._internal.batch.delete_record", side_effect=mock_delete):
            result = await batch_delete(
                mock_client,
                uris,
                concurrency=5,
                show_progress=False,
            )

        assert len(result.successful) == 20
        assert max_concurrent <= 5

    async def test_batch_delete_empty_list(self, mock_client: AsyncClient) -> None:
        """test batch delete with empty URI list."""
        result = await batch_delete(
            mock_client,
            [],
            show_progress=False,
        )

        assert len(result.successful) == 0
        assert len(result.failed) == 0
        assert result.total == 0


class TestBatchResult:
    """tests for BatchResult dataclass."""

    def test_batch_result_properties(self) -> None:
        """test BatchResult property calculations."""
        result = BatchResult(
            successful=["uri1", "uri2", "uri3"],
            failed=[("uri4", ValueError("error"))],
        )

        assert result.total == 4
        assert result.success_rate == 75.0

    def test_batch_result_empty(self) -> None:
        """test BatchResult with no operations."""
        result = BatchResult(successful=[], failed=[])

        assert result.total == 0
        assert result.success_rate == 0.0


class TestReadUrisFromStdin:
    """tests for read_uris_from_stdin function."""

    def test_read_from_stdin(self) -> None:
        """test reading URIs from stdin."""
        import io

        test_input = "uri1\nuri2\nuri3\n"

        with (
            patch("sys.stdin", io.StringIO(test_input)),
            patch("sys.stdin.isatty", return_value=False),
        ):
            uris = read_uris_from_stdin()

        assert uris == ["uri1", "uri2", "uri3"]

    def test_read_from_stdin_with_empty_lines(self) -> None:
        """test reading URIs from stdin with empty lines."""
        import io

        test_input = "uri1\n\nuri2\n  \nuri3\n"

        with (
            patch("sys.stdin", io.StringIO(test_input)),
            patch("sys.stdin.isatty", return_value=False),
        ):
            uris = read_uris_from_stdin()

        assert uris == ["uri1", "uri2", "uri3"]

    def test_read_from_stdin_strips_whitespace(self) -> None:
        """test reading URIs from stdin strips whitespace."""
        import io

        test_input = "  uri1  \n  uri2\nuri3  \n"

        with (
            patch("sys.stdin", io.StringIO(test_input)),
            patch("sys.stdin.isatty", return_value=False),
        ):
            uris = read_uris_from_stdin()

        assert uris == ["uri1", "uri2", "uri3"]

    def test_read_from_tty_returns_empty(self) -> None:
        """test reading from TTY returns empty list."""
        with patch("sys.stdin.isatty", return_value=True):
            uris = read_uris_from_stdin()

        assert uris == []
