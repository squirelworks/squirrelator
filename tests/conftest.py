"""Shared test fixtures."""

import json
import shutil

import pytest

from squirrelator import data

# The "markers" values proposed for data v0.1.1, for the languages tested here.
MARKERS = {
    "english": {"default": "before", "@possessive": "after"},
    "japanese": {"default": "after"},
    "hangul": {"default": "after"},
    "chinese": {"default": "before", "@possessive": "after"},
    "latin": {"default": "before"},
}


@pytest.fixture(scope="session")
def root(tmp_path_factory):
    """A copy of the data with "markers" filled in, until the pinned data has it."""
    out = tmp_path_factory.mktemp("data")
    shutil.copytree(data.data_dir() / "meaning", out / "meaning")
    for lang, markers in MARKERS.items():
        shutil.copytree(data.data_dir() / "languages" / lang, out / "languages" / lang)
        meta_path = out / "languages" / lang / "meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta.setdefault("markers", markers)
        meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    (out / "features.json").write_text("{}", encoding="utf-8")
    return out


