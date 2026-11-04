"""Analyze: turn source text into tokens, using the language's word list.

- Space-separated languages are split into words, numbers and punctuation.
  A phrase the word list has as one entry ("Γεια σου") stays one token.
- Languages written without spaces (Japanese, Chinese, Thai) are segmented
  into the fewest known words.
- A word the list doesn't have is split into a known stem and the prefixes
  and suffixes the data lists ("اسمك" is اسم + -ك, "저는" is 저 + -는), but
  only when every part is known.

Every token says whether the data knows it, so later stages mark unknown
words instead of guessing. Dictionary forms of inflected words come in a
later PR, once squirrel-lang-data has inflection tables.
"""

import unicodedata
from dataclasses import dataclass

from ..lexicon import Entry, Lexicon, lexicon

# Between two letters these stay inside the word: apostrophes, hyphens and
# the Armenian emphasis, exclamation and question marks (ի՞նչ).
JOINERS = set("'’-՛՜՞")
# How many words a phrase in a spaced language's word list can span.
MAX_PHRASE = 4
# Segmenting cost of a character no word covers, against 1 per known word.
UNKNOWN_COST = 3


@dataclass(frozen=True)
class Token:
    text: str
    start: int                 # character offsets into the source
    end: int
    kind: str                  # "word", "number", "punct" or "space"
    entries: tuple[Entry, ...] = ()
    affix: str = ""            # "prefix" or "suffix" for a split-off affix

    @property
    def known(self) -> bool:
        return self.kind != "word" or bool(self.entries)


def _kind(ch: str, letters: frozenset[str] = frozenset()) -> str:
    """word for letters and combining marks (so Indic vowel signs and viramas
    stay with their letters), number, space, or punct for the rest."""
    if ch in letters:
        return "word"
    if ch.isspace():
        return "space"
    cat = unicodedata.category(ch)
    if cat[0] in "LM":
        return "word"
    if cat[0] == "N":
        return "number"
    return "punct"


def _runs(text: str, letters: frozenset[str] = frozenset()) -> list[tuple[str, int, int]]:
    """(kind, start, end) runs. Punctuation is one character per run; a
    joiner between two letters belongs to the word."""
    runs, i = [], 0
    while i < len(text):
        kind = _kind(text[i], letters)
        j = i + 1
        if kind != "punct":
            while j < len(text):
                if _kind(text[j], letters) == kind:
                    j += 1
                elif (kind == "word" and text[j] in JOINERS and j + 1 < len(text)
                      and _kind(text[j + 1], letters) == "word"):
                    j += 2
                else:
                    break
        runs.append((kind, i, j))
        i = j
    return runs


def _segment(text: str, offset: int, lex: Lexicon, *, whole_word: bool) -> list[Token] | None:
    """Split a run of letters into the fewest known pieces. With whole_word
    (a spaced language's word), a prefix may start it and suffixes may follow
    a stem, and the result is None unless every piece is known. Otherwise
    characters no piece covers are grouped into unknown words."""
    n = len(text)
    # best[i] = (cost, pieces) for text[:i]; a piece is (start, end, entries, affix)
    best: list[tuple[int, list] | None] = [None] * (n + 1)
    best[0] = (0, [])
    for i in range(n):
        if best[i] is None:
            continue
        cost, pieces = best[i]
        has_stem = any(not p[3] for p in pieces)
        for j in range(min(n, i + lex.longest), i, -1):
            piece = text[i:j]
            # Affixes first: after a stem, 은 is the topic suffix, not the
            # word for silver, when both split the word equally well.
            options = []
            if whole_word and i == 0 and j < n:
                options.append((lex.prefix(piece), "prefix"))
            if whole_word and has_stem:
                options.append((lex.suffix(piece), "suffix"))
            options.append((lex.lookup(piece), ""))
            for entries, affix in options:
                if entries and (best[j] is None or cost + 1 < best[j][0]):
                    best[j] = (cost + 1, pieces + [(i, j, entries, affix)])
        if not whole_word and (best[i + 1] is None or cost + UNKNOWN_COST < best[i + 1][0]):
            best[i + 1] = (cost + UNKNOWN_COST, pieces + [(i, i + 1, (), "")])
    if best[n] is None:
        return None
    tokens: list[Token] = []
    for start, end, entries, affix in best[n][1]:
        if not entries and tokens and not tokens[-1].entries:
            start = tokens.pop().start - offset  # join neighbouring unknown characters
        tokens.append(Token(text[start:end], offset + start, offset + end, "word", entries, affix))
    return tokens


def _spaced(text: str, lex: Lexicon) -> list[Token]:
    runs = _runs(text, lex.letters)
    tokens, r = [], 0
    while r < len(runs):
        kind, start, end = runs[r]
        if kind != "word":
            tokens.append(Token(text[start:end], start, end, kind))
            r += 1
            continue
        # The longest phrase from the word list starting here, e.g. "Γεια σου".
        found, last = lex.lookup(text[start:end]), r
        for k in range(r + 2, min(len(runs), r + 2 * MAX_PHRASE - 1), 2):
            if runs[k][0] != "word" or text[runs[k - 1][1]:runs[k - 1][2]] != " ":
                break
            if entries := lex.lookup(text[start:runs[k][2]]):
                found, last = entries, k
        end = runs[last][2]
        word = text[start:end]
        if found:
            tokens.append(Token(word, start, end, "word", found))
        else:
            tokens += _segment(word, start, lex, whole_word=True) or [Token(word, start, end, "word")]
        r = last + 1
    return tokens


def _unspaced(text: str, lex: Lexicon) -> list[Token]:
    tokens = []
    for kind, start, end in _runs(text, lex.letters):
        if kind == "word":
            tokens += _segment(text[start:end], start, lex, whole_word=False)
        else:
            tokens.append(Token(text[start:end], start, end, kind))
    return tokens


def analyze(text: str, language: str, *, lex: Lexicon | None = None) -> list[Token]:
    """Tokens for text in a squirrel-lang-data language. Offsets cover the
    whole text, so joining every token's text gives the source back."""
    lex = lex or lexicon(language)
    return (_spaced if lex.spaced else _unspaced)(text, lex)
