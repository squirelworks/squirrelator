"""The meaning matrix from squirrel-lang-data (meaning/).

sentences.jsonl lists each row's content meanings; columns/<id>.jsonl gives
one language's rendering of each row, token by token, plus the meanings
that language leaves implied (Japanese usually drops "I"). From the columns
this module also counts which grammar marker goes with which content
meaning, so で after バス reads as @means and に after 学校 as @direction.
"""

import json
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .data import data_dir


@dataclass(frozen=True)
class Row:
    id: str
    en: str
    meanings: tuple[str, ...]                 # content meanings, in the data's order
    implied: dict[str, tuple[str, ...]]       # language -> meanings it leaves unsaid


@dataclass(frozen=True)
class Matrix:
    rows: dict[str, Row]
    # (content meaning, grammar meaning) -> how often a column marks it so
    pairs: Counter

    def marker_weight(self, content: str, grammar: str) -> int:
        return self.pairs.get((content, grammar), 0)


def _lines(path: Path):
    if not path.is_file():
        return []
    rows = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(r) for r in rows[1:] if r.strip()]


@lru_cache(maxsize=None)
def _load(root: Path) -> Matrix:
    base = root / "meaning"
    rows = {r["id"]: r for r in _lines(base / "sentences.jsonl")}
    implied: dict[str, dict[str, tuple[str, ...]]] = {i: {} for i in rows}
    pairs: Counter = Counter()
    for path in sorted((base / "columns").glob("*.jsonl")):
        for row in _lines(path):
            if row.get("sentence") in implied and row.get("implied"):
                implied[row["sentence"]][path.stem] = tuple(row["implied"])
            tokens = [t[2] for t in row.get("t", [])]
            for i, m in enumerate(tokens):
                if not m.startswith("@"):
                    continue
                # A marker counts for the content meanings right next to it.
                for j in (i - 1, i + 1):
                    if 0 <= j < len(tokens) and not tokens[j].startswith("@"):
                        pairs[(tokens[j], m)] += 1
    return Matrix(
        {i: Row(i, r.get("en", ""), tuple(r.get("m", [])), implied[i]) for i, r in rows.items()},
        pairs,
    )


def matrix(root: Path | str | None = None) -> Matrix:
    """The meaning matrix, loaded once per data checkout."""
    return _load(data_dir(root).resolve())
