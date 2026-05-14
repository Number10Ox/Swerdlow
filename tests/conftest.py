"""Shared pytest fixtures for swerdlow tests."""
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_dir():
    """Path to the tests/fixtures/ directory."""
    return FIXTURES
