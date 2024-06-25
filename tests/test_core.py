"""Test module for test core module."""

from z3_armor import hello


def test_hello() -> None:
    """Test basic."""
    assert hello("World") == "Hello World"
    assert hello("") == "Hello"
