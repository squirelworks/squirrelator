import re
from pathlib import Path

import squirrelator


def test_version_matches_pyproject():
    # The Draft release workflow checks pyproject.toml; the package must agree.
    text = (Path(__file__).resolve().parent.parent / "pyproject.toml").read_text(encoding="utf-8")
    version = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M).group(1)
    assert squirrelator.__version__ == version
