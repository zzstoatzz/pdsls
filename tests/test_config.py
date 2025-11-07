"""tests for configuration."""

from __future__ import annotations

import os

from pdsx._internal.config import Settings


def test_settings_defaults() -> None:
    """test default settings values when no env vars are set."""
    # clear env vars for this test
    old_values = {}
    for key in ["ATPROTO_PDS_URL", "ATPROTO_HANDLE", "ATPROTO_PASSWORD"]:
        old_values[key] = os.environ.pop(key, None)

    try:
        settings = Settings(_env_file=None)
        assert settings.atproto_pds_url == "https://bsky.social"
        assert settings.atproto_handle == ""
        assert settings.atproto_password == ""
    finally:
        # restore env vars
        for key, value in old_values.items():
            if value is not None:
                os.environ[key] = value


def test_settings_override() -> None:
    """test overriding settings."""
    settings = Settings(
        atproto_pds_url="https://custom.pds",
        atproto_handle="test.handle",
        atproto_password="test_password",
    )
    assert settings.atproto_pds_url == "https://custom.pds"
    assert settings.atproto_handle == "test.handle"
    assert settings.atproto_password == "test_password"
