"""Word lists read from squirrel-lang-data.

A Lexicon maps the written forms of one language's words to what the data
says about them: the vocabulary decks (languages/<id>/vocab.jsonl) and the
meaning-matrix column (meaning/columns/<id>.jsonl), whose tokens point at
meaning units, and the inflected forms in languages/<id>/inflections.jsonl. English comes from the "en" lists of meaning/meanings.jsonl, plus its inflected forms.

squirrelator never keeps its own copy of these words; see AGENTS.md.
"""

import json
import unicodedata
from dataclasses import dataclass, field
from functools import cached_property, lru_cache
from pathlib import Path

from .data import data_dir
from .inflections import inflections


@dataclass(frozen=True)
class Entry:
    """What the data says about one written form."""

    word: str              # as the data writes it
    reading: str = ""      # kana, pinyin, romanization, when the data has one
    gloss: str = ""        # English meaning, from the vocabulary
    meaning: str = ""      # meaning unit id from the meaning matrix, if any
    source: str = ""       # "vocab", "column", "meanings", "phrasings" or "inflections"


def fold(text: str) -> str:
    """The key words are matched by: case-folded, with Latin and Greek
    accents (U+0300 to U+036F) removed, so "salve" finds "salvē". Other
    marks, such as kana voicing or Indic vowel signs, are kept."""
    decomposed = unicodedata.normalize("NFD", text.casefold())
    stripped = "".join(c for c in decomposed if not 0x300 <= ord(c) <= 0x36F)
    return unicodedata.normalize("NFC", stripped)


def _jsonl(path: Path):
    """Entries of a JSONL content file, skipping its header line."""
    if not path.is_file():
        return
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if line and i > 0:
                yield json.loads(line)


def _header(path: Path) -> dict:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.loads(f.readline() or "{}")


@dataclass(frozen=True)
class Lexicon:
    language: str
    spaced: bool                       # False for scripts written without spaces
    entries: dict[str, tuple[Entry, ...]]
    longest: int                       # longest key, in characters
    # Affixes the data writes with a hyphen ("ال-", "-ك", "-는"), by their
    # letters only. A prefix only starts a word; a suffix only follows a stem.
    prefixes: dict[str, tuple[Entry, ...]] = field(default_factory=dict)
    suffixes: dict[str, tuple[Entry, ...]] = field(default_factory=dict)

    @cached_property
    def letters(self) -> frozenset[str]:
        """Characters that are letters in this language although Unicode
        calls them punctuation: the apostrophe, when the word list often
        starts or ends words with it (Klingon writes a glottal stop: Qapla')."""
        keys = [*self.entries, *self.prefixes, *self.suffixes]
        edged = sum(1 for k in keys if k[0] in "'’" or k[-1] in "'’")
        return frozenset("'’") if keys and edged >= 0.02 * len(keys) else frozenset()

    def lookup(self, text: str) -> tuple[Entry, ...]:
        return self.entries.get(fold(text), ())

    def prefix(self, text: str) -> tuple[Entry, ...]:
        return self.prefixes.get(fold(text), ())

    def suffix(self, text: str) -> tuple[Entry, ...]:
        return self.suffixes.get(fold(text), ())

    def __contains__(self, text: str) -> bool:
        return fold(text) in self.entries


def available(root: Path | None = None) -> list[str]:
    """Language ids the data has a vocabulary or a meaning column for."""
    root = data_dir(root)
    ids = {p.parent.name for p in (root / "languages").glob("*/vocab.jsonl")}
    ids |= {p.stem for p in (root / "meaning" / "columns").glob("*.jsonl")}
    return sorted(ids | {"english"})


@lru_cache(maxsize=None)
def _load(language: str, root: Path) -> Lexicon:
    found: dict[str, list[Entry]] = {}
    prefixes: dict[str, list[Entry]] = {}
    suffixes: dict[str, list[Entry]] = {}

    def add(form: str, entry: Entry):
        form = form.strip()
        table = found
        if len(form) > 1 and form.endswith("-") and not form.startswith("-"):
            table, form = prefixes, form[:-1]
        elif len(form) > 1 and form.startswith("-") and not form.endswith("-"):
            table, form = suffixes, form[1:]
        key = fold(form)
        if key and entry not in table.setdefault(key, []):
            table[key].append(entry)

    column = root / "meaning" / "columns" / f"{language}.jsonl"
    spaced = _header(column).get("sep", " ") != ""

    if language == "english":
        for m in _jsonl(root / "meaning" / "meanings.jsonl"):
            for form in m.get("en", []):
                add(form, Entry(form, meaning=m["id"], source="meanings"))
        # English that carries a meaning only next to others ("take" the bus).
        for p in _jsonl(root / "meaning" / "phrasings.jsonl"):
            for form in p.get("en", []):
                add(form, Entry(form, meaning=p["m"], source="phrasings"))
    else:
        for v in _jsonl(root / "languages" / language / "vocab.jsonl"):
            add(v["word"], Entry(v["word"], v.get("reading", ""), v.get("meaning", ""), source="vocab"))
        for row in _jsonl(column):
            for text, reading, meaning in row.get("t", []):
                add(text, Entry(text, reading, meaning=meaning, source="column"))

    # Inflected forms the lists above don't have (行きました, reads): the
    # word's meaning joined with the meanings the form adds, as columns join
    # them ("go+@polite+@past"), so later stages read both.
    for word in inflections(language, root):
        for form in word.forms:
            if fold(form.text) not in found:
                meaning = "+".join([word.meaning, *sorted(form.features)])
                add(form.text, Entry(form.text, form.reading, meaning=meaning, source="inflections"))

    def freeze(table):
        return {k: tuple(v) for k, v in table.items()}

    entries = freeze(found)
    longest = max(map(len, [*entries, *prefixes, *suffixes]), default=0)
    return Lexicon(language, spaced, entries, longest, freeze(prefixes), freeze(suffixes))


def lexicon(language: str, root: Path | str | None = None) -> Lexicon:
    """The Lexicon for a squirrel-lang-data language id, loaded once."""
    return _load(language, data_dir(root).resolve())


@lru_cache(maxsize=None)
def _meta(language: str, root: Path) -> dict:
    path = root / "languages" / language / "meta.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def language_meta(language: str, root: Path | str | None = None) -> dict:
    """A language's meta.json from the data, or {} when it has none."""
    return _meta(language, data_dir(root).resolve())
