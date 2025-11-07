"""tests for operations module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from atproto import AsyncClient, models

from pdsls._internal.operations import delete_record, update_record


@pytest.fixture
def mock_client() -> AsyncClient:
    """create a mock atproto client."""
    client = MagicMock()
    client.me = MagicMock()
    client.me.did = "did:plc:test123"
    return client


@pytest.fixture
def mock_client_no_auth() -> AsyncClient:
    """create a mock atproto client without authentication."""
    client = MagicMock()
    client.me = None
    return client


class TestUpdateRecord:
    """tests for update_record function."""

    async def test_full_uri_format(self, mock_client: AsyncClient) -> None:
        """test update with full at:// URI format."""
        mock_client.com.atproto.repo.get_record = AsyncMock(  # type: ignore[attr-defined]
            return_value=MagicMock(value={"description": "old bio"})
        )
        mock_client.com.atproto.repo.put_record = AsyncMock(  # type: ignore[attr-defined]
            return_value=models.ComAtprotoRepoPutRecord.Response(
                uri="at://did:plc:test123/app.bsky.actor.profile/self",
                cid="testcid",
            )
        )

        result = await update_record(
            mock_client,
            "at://did:plc:test123/app.bsky.actor.profile/self",
            {"description": "new bio"},
        )

        assert result.uri == "at://did:plc:test123/app.bsky.actor.profile/self"
        mock_client.com.atproto.repo.put_record.assert_called_once()

    async def test_shorthand_uri_format(self, mock_client: AsyncClient) -> None:
        """test update with shorthand URI format (collection/rkey)."""
        mock_client.com.atproto.repo.get_record = AsyncMock(  # type: ignore[attr-defined]
            return_value=MagicMock(value={"description": "old bio"})
        )
        mock_client.com.atproto.repo.put_record = AsyncMock(  # type: ignore[attr-defined]
            return_value=models.ComAtprotoRepoPutRecord.Response(
                uri="at://did:plc:test123/app.bsky.actor.profile/self",
                cid="testcid",
            )
        )

        await update_record(
            mock_client,
            "app.bsky.actor.profile/self",
            {"description": "new bio"},
        )

        # verify it used client.me.did
        mock_client.com.atproto.repo.get_record.assert_called_once()
        call_args = mock_client.com.atproto.repo.get_record.call_args[0][0]
        assert call_args["repo"] == "did:plc:test123"
        assert call_args["collection"] == "app.bsky.actor.profile"
        assert call_args["rkey"] == "self"

    async def test_shorthand_uri_without_auth_fails(
        self, mock_client_no_auth: AsyncClient
    ) -> None:
        """test shorthand URI fails without authentication."""
        with pytest.raises(ValueError, match="shorthand URI requires authentication"):
            await update_record(
                mock_client_no_auth,
                "app.bsky.actor.profile/self",
                {"description": "new bio"},
            )

    async def test_invalid_uri_format_fails(self, mock_client: AsyncClient) -> None:
        """test invalid URI format raises error."""
        with pytest.raises(ValueError, match="invalid URI format"):
            await update_record(
                mock_client,
                "invalid/uri/format/too/many/parts",
                {"description": "new bio"},
            )


class TestDeleteRecord:
    """tests for delete_record function."""

    async def test_full_uri_format(self, mock_client: AsyncClient) -> None:
        """test delete with full at:// URI format."""
        mock_client.com.atproto.repo.delete_record = AsyncMock()  # type: ignore[attr-defined]

        await delete_record(
            mock_client,
            "at://did:plc:test123/app.bsky.feed.post/abc123",
        )

        mock_client.com.atproto.repo.delete_record.assert_called_once()
        call_args = mock_client.com.atproto.repo.delete_record.call_args[0][0]
        assert call_args["repo"] == "did:plc:test123"
        assert call_args["collection"] == "app.bsky.feed.post"
        assert call_args["rkey"] == "abc123"

    async def test_shorthand_uri_format(self, mock_client: AsyncClient) -> None:
        """test delete with shorthand URI format (collection/rkey)."""
        mock_client.com.atproto.repo.delete_record = AsyncMock()  # type: ignore[attr-defined]

        await delete_record(
            mock_client,
            "app.bsky.feed.post/abc123",
        )

        # verify it used client.me.did
        mock_client.com.atproto.repo.delete_record.assert_called_once()
        call_args = mock_client.com.atproto.repo.delete_record.call_args[0][0]
        assert call_args["repo"] == "did:plc:test123"
        assert call_args["collection"] == "app.bsky.feed.post"
        assert call_args["rkey"] == "abc123"

    async def test_shorthand_uri_without_auth_fails(
        self, mock_client_no_auth: AsyncClient
    ) -> None:
        """test shorthand URI fails without authentication."""
        with pytest.raises(ValueError, match="shorthand URI requires authentication"):
            await delete_record(
                mock_client_no_auth,
                "app.bsky.feed.post/abc123",
            )

    async def test_invalid_uri_format_fails(self, mock_client: AsyncClient) -> None:
        """test invalid URI format raises error."""
        with pytest.raises(ValueError, match="invalid URI format"):
            await delete_record(
                mock_client,
                "invalid",
            )
