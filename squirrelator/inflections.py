"""Inflection tables from squirrel-lang-data (languages/<id>/inflections.jsonl).

Each word lists its lemma, the content meaning it carries, and its forms,
each tagged with the meanings the form adds (行きました adds @polite and
@past to go). Analyze reads the tables to know an inflected form; Generate
reads them to pick the form a clause needs.
"""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .data import data_dir


@dataclass(frozen=True)
class Form:
    name: str
    text: str
    reading: str
    features: frozenset[str]


@dataclass(frozen=True)
class Word:
    lemma: str
    reading: str
    meaning: str
    forms: tuple[Form, ...]

    def form(self, name: str) -> Form | None:
        return next((f for f in self.forms if f.name == name), None)


@lru_cache(maxsize=None)
def _load(language: str, root: Path) -> tuple[Word, ...]:
    path = root / "languages" / language / "inflections.jsonl"
    if not path.is_file():
        return ()
    lines = path.read_text(encoding="utf-8").splitlines()[1:]
    return tuple(
        Word(w["lemma"], w.get("reading", ""), w["m"], tuple(
            Form(f["name"], f["text"], f.get("reading", ""), frozenset(f.get("features", [])))
            for f in w.get("forms", [])))
        for w in map(json.loads, filter(str.strip, lines)))


def inflections(language: str, root: Path | str | None = None) -> tuple[Word, ...]:
    """A language's inflection tables, or () when the data has none."""
    return _load(language, data_dir(root).resolve())
