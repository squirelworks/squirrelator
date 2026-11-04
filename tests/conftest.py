"""Shared test fixtures."""

import pytest

from squirrelator import data

# Languages whose meta.json "markers" the parse and interlingua tests cover.
LANGUAGES = ("english", "japanese", "hangul", "chinese", "latin")


@pytest.fixture(scope="session")
def root():
    """The pinned squirrel-lang-data checkout."""
    return data.data_dir()
