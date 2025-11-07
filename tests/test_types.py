"""tests for type aliases."""

from __future__ import annotations

from pdsx._internal.types import RecordValue


def test_record_value_type_alias() -> None:
    """test that RecordValue accepts valid types."""
    valid_values: list[RecordValue] = [
        "string",
        42,
        3.14,
        True,
        False,
        None,
    ]
    assert len(valid_values) == 6
