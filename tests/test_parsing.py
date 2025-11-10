"""tests for argument parsing."""

from __future__ import annotations

import pytest

from pdsx._internal.parsing import parse_key_value_args


def test_parse_string_values() -> None:
    """test parsing string values."""
    result = parse_key_value_args(["name=test", "description=hello world"])
    assert result == {"name": "test", "description": "hello world"}


def test_parse_boolean_values() -> None:
    """test parsing boolean values."""
    result = parse_key_value_args(["active=true", "disabled=false"])
    assert result == {"active": True, "disabled": False}


def test_parse_null_values() -> None:
    """test parsing null values."""
    result = parse_key_value_args(["value=null"])
    assert result == {"value": None}


def test_parse_integer_values() -> None:
    """test parsing integer values."""
    result = parse_key_value_args(["count=42", "limit=100"])
    assert result == {"count": 42, "limit": 100}


def test_parse_float_values() -> None:
    """test parsing float values."""
    result = parse_key_value_args(["rate=3.14", "score=99.9"])
    assert result == {"rate": 3.14, "score": 99.9}


def test_parse_mixed_values() -> None:
    """test parsing mixed value types."""
    result = parse_key_value_args(
        [
            "name=test",
            "count=5",
            "active=true",
            "value=null",
            "rate=2.5",
        ]
    )
    assert result == {
        "name": "test",
        "count": 5,
        "active": True,
        "value": None,
        "rate": 2.5,
    }


def test_invalid_format_raises_system_exit() -> None:
    """test that invalid format raises SystemExit."""
    with pytest.raises(SystemExit):
        parse_key_value_args(["invalid"])


def test_parse_json_object() -> None:
    """test parsing JSON object values."""
    result = parse_key_value_args(['embed={"$type":"blob","size":123}'])
    assert result == {"embed": {"$type": "blob", "size": 123}}


def test_parse_json_array() -> None:
    """test parsing JSON array values."""
    result = parse_key_value_args(['tags=["python","atproto"]'])
    assert result == {"tags": ["python", "atproto"]}


def test_parse_complex_nested_json() -> None:
    """test parsing complex nested JSON."""
    result = parse_key_value_args(
        [
            'reply={"root":{"uri":"at://...","cid":"..."},"parent":{"uri":"at://...","cid":"..."}}'
        ]
    )
    assert result == {
        "reply": {
            "root": {"uri": "at://...", "cid": "..."},
            "parent": {"uri": "at://...", "cid": "..."},
        }
    }


def test_parse_mixed_primitive_and_json() -> None:
    """test parsing mix of primitives and JSON values."""
    result = parse_key_value_args(
        ["text=hello", "count=5", 'meta={"version":1}', "active=true"]
    )
    assert result == {
        "text": "hello",
        "count": 5,
        "meta": {"version": 1},
        "active": True,
    }


def test_invalid_json_raises_system_exit() -> None:
    """test that invalid JSON raises system exit."""
    with pytest.raises(SystemExit):
        parse_key_value_args(["embed={invalid json}"])
