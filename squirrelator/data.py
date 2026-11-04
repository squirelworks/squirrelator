"""Find the squirrel-lang-data checkout the engine reads its language data from.

Order, first match wins:

1. a path passed to data_dir() directly;
2. the SQUIRREL_LANG_DATA environment variable, so LanguageStudentDesk can
   hand squirrelator its own data/ checkout and only one copy exists;
3. the data/ submodule next to this package in a squirrelator checkout.

squirrelator never keeps its own copy of the data; see AGENTS.md.
"""

import os
from pathlib import Path

ENV_VAR = "SQUIRREL_LANG_DATA"
SUBMODULE = Path(__file__).resolve().parent.parent / "data"
# A file every squirrel-lang-data release has at its root.
MARKER = "features.json"


class DataNotFound(FileNotFoundError):
    """No squirrel-lang-data checkout was found."""


def _usable(path: Path) -> bool:
    return (path / MARKER).is_file()


def data_dir(path: str | os.PathLike | None = None) -> Path:
    """Return the squirrel-lang-data folder, or raise DataNotFound."""
    if path is not None:
        p = Path(path).expanduser()
        if not _usable(p):
            raise DataNotFound(f"{p} is not a squirrel-lang-data checkout (no {MARKER})")
        return p
    env = os.environ.get(ENV_VAR)
    if env:
        p = Path(env).expanduser()
        if not _usable(p):
            raise DataNotFound(
                f"{ENV_VAR}={env} is not a squirrel-lang-data checkout (no {MARKER})"
            )
        return p
    if _usable(SUBMODULE):
        return SUBMODULE
    raise DataNotFound(
        "squirrel-lang-data not found. Run `git submodule update --init`, "
        f"or set {ENV_VAR} to a squirrel-lang-data checkout."
    )
