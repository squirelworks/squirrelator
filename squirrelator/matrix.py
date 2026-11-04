"""The meaning matrix from squirrel-lang-data (meaning/).

sentences.jsonl lists each row's content meanings; columns/<id>.jsonl gives
one language's rendering of each row, token by token, plus the meanings
that language leaves implied (Japanese usually drops "I"). From the columns
this module also counts which grammar marker goes with which content
meaning, so で after バス reads as @means and に after 学校 as @direction.
"""

import json
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from .data import data_dir


@dataclass(frozen=True)
class Row:
    id: str
    en: str
    meanings: tuple[str, ...]                 # content meanings, in the data's order
    implied: dict[str, tuple[str, ...]]       # language -> meanings it leaves unsaid
    also: tuple[str, ...] = ()                # other English wordings of the row


@dataclass(frozen=True)
class Rendering:
    """One language's column for one row: tokens [text, reading, meanings]."""
    tokens: tuple[tuple[str, str, str], ...]
    end: str
    sep: str


@dataclass(frozen=True)
class Matrix:
    rows: dict[str, Row]
    # (content meaning, grammar meaning) -> how often a column marks it so
    pairs: Counter
    # language -> row id -> that language's rendering of the row
    columns: dict[str, dict[str, Rendering]] = field(default_factory=dict)
    # language -> meaning id -> Counter of (text, reading) that carry it alone
    words: dict[str, dict[str, Counter]] = field(default_factory=dict)
    # meaning id -> its English words, from meanings.jsonl
    english: dict[str, tuple[str, ...]] = field(default_factory=dict)
    # language -> meaning id -> where in a sentence the language puts it,
    # from 0 (first) to 1 (last), averaged over the rows that have it
    order: dict[str, dict[str, float]] = field(default_factory=dict)

    def marker_weight(self, content: str, grammar: str) -> int:
        return self.pairs.get((content, grammar), 0)

    def word(self, language: str, meaning: str) -> tuple[str, str] | None:
        """The (text, reading) a language's column most often uses for a
        meaning on its own, or None when the column never does."""
        counts = self.words.get(language, {}).get(meaning)
        return counts.most_common(1)[0][0] if counts else None


def _lines(path: Path):
    if not path.is_file():
        return []
    rows = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(r) for r in rows[1:] if r.strip()]


def _order(sentences) -> dict[str, float]:
    """Mean relative position of each meaning; each sentence is a list of
    slots, each slot the meanings found there."""
    sums: dict[str, list[float]] = {}
    for slots in sentences:
        slots = list(slots)
        for i, meanings in enumerate(slots):
            for m in meanings:
                sums.setdefault(m, []).append(i / max(1, len(slots) - 1))
    return {m: sum(v) / len(v) for m, v in sums.items()}


def _english_positions(en: str, english: dict[str, tuple[str, ...]]):
    """The words of an English sentence, each with the meanings whose
    English words it is ("school" -> school)."""
    words = [w.strip(".,!?").casefold() for w in en.split()]
    by_word: dict[str, list[str]] = {}
    for m, forms in english.items():
        for f in forms:
            by_word.setdefault(f.casefold(), []).append(m)
    return [by_word.get(w, []) for w in words]


def _header(path: Path) -> dict:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.loads(f.readline() or "{}")


@lru_cache(maxsize=None)
def _load(root: Path) -> Matrix:
    base = root / "meaning"
    rows = {r["id"]: r for r in _lines(base / "sentences.jsonl")}
    implied: dict[str, dict[str, tuple[str, ...]]] = {i: {} for i in rows}
    pairs: Counter = Counter()
    columns: dict[str, dict[str, Rendering]] = {}
    words: dict[str, dict[str, Counter]] = {}
    for path in sorted((base / "columns").glob("*.jsonl")):
        sep = _header(path).get("sep", " ")
        lang_cols, lang_words = columns.setdefault(path.stem, {}), words.setdefault(path.stem, {})
        for row in _lines(path):
            tokens_full = tuple(tuple(t[:3]) for t in row.get("t", []))
            if row.get("sentence") in rows:
                lang_cols[row["sentence"]] = Rendering(tokens_full, row.get("end", ""), sep)
            for text, reading, m in tokens_full:
                if "+" not in m:
                    lang_words.setdefault(m, Counter())[(text, reading)] += 1
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
    english = {m["id"]: tuple(m.get("en", [])) for m in _lines(base / "meanings.jsonl")}
    order = {lang: _order((list(t[2].split("+")) for t in r.tokens) for r in cols.values())
             for lang, cols in columns.items()}
    order["english"] = _order(_english_positions(r.get("en", ""), english) for r in rows.values())
    return Matrix(
        {i: Row(i, r.get("en", ""), tuple(r.get("m", [])), implied[i], tuple(r.get("also", [])))
         for i, r in rows.items()},
        pairs, columns, words, english, order,
    )


def matrix(root: Path | str | None = None) -> Matrix:
    """The meaning matrix, loaded once per data checkout."""
    return _load(data_dir(root).resolve())
