"""tests for cli module."""

from __future__ import annotations

import subprocess


def test_version_flag_long() -> None:
    """test --version flag displays version."""
    result = subprocess.run(
        ["pdsx", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    output = result.stdout.strip()
    assert output.startswith("pdsx ")


def test_version_flag_short() -> None:
    """test -v flag displays version."""
    result = subprocess.run(
        ["pdsx", "-v"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    output = result.stdout.strip()
    assert output.startswith("pdsx ")
