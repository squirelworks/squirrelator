"""Parse: group a sentence's tokens into clauses and phrases.

A phrase is one content word (its head) plus the grammar markers that belong
to it: the particle after a Japanese noun (学校 + に), the preposition and
article before an English one (to + the + school), or an affix split off by
Analyze (저 + -는). Which side a separate marker sits on comes from the
language's "markers" field in squirrel-lang-data (languages/<id>/meta.json);
affixes show their own side. A marker that can't be placed, because the data
doesn't say or no content word is there, is kept as a feature of the whole
clause rather than guessed onto a word.

Clauses end at sentence punctuation. A question mark adds "@question" to the
clause's features.
"""

from dataclasses import dataclass

from ..lexicon import language_meta
from .analyze import Token

CLAUSE_END = set(".!?。！？؟;；")
QUESTION = set("?？؟")


def meaning_of(token: Token) -> str:
    """The meaning unit id a token carries, or "" when the data gives none."""
    return next((e.meaning for e in token.entries if e.meaning), "")


def meanings_of(token: Token) -> tuple[str, ...]:
    """Every meaning unit id the data gives a token, first one first. で is
    both @place and @means; Interlingua picks between them."""
    return tuple(dict.fromkeys(e.meaning for e in token.entries if e.meaning))


def is_marker(token: Token) -> bool:
    return meaning_of(token).startswith("@")


@dataclass(frozen=True)
class Phrase:
    head: Token
    markers: tuple[Token, ...] = ()

    @property
    def meaning(self) -> str:
        return meaning_of(self.head)

    @property
    def roles(self) -> tuple[tuple[str, ...], ...]:
        """For each marker, in written order, the grammar meanings it can
        carry (one or more)."""
        return tuple(tuple(m for m in meanings_of(t) if m.startswith("@")) for t in self.markers)


@dataclass(frozen=True)
class Clause:
    tokens: tuple[Token, ...]
    phrases: tuple[Phrase, ...]
    features: tuple[str, ...] = ()       # clause-wide grammar meanings

    @property
    def unknown(self) -> tuple[Token, ...]:
        return tuple(t for t in self.tokens if not t.known)


def _sides(language: str, root) -> tuple[str | None, dict]:
    markers = language_meta(language, root).get("markers") or {}
    return markers.get("default"), markers


def _role(token: Token) -> str:
    """The grammar meaning a word carries as a marker: its first meaning, or
    for a word that is first a content word (います), the grammar meaning
    its column gives it."""
    if is_marker(token):
        return meaning_of(token)
    return next(e.meaning for e in token.entries if e.meaning.startswith("@") and e.source == "column")


def _acts_as_marker(t: Token, words: list[Token], i: int, default, sides: dict, last) -> bool:
    """Whether a word is read as a grammar marker. A word the data gives only
    grammar meanings always is. A word the language's matrix column writes
    with both kinds (います is exist and
    @ongoing, 坐 is sit and @means) is a marker only when a content word sits
    right where the marker attaches: just before it for an "after" marker
    (住んで います), just after it for a "before" one (坐 火车). After a
    particle (猫が います) or with nothing to attach to (请坐) it is a word."""
    ms = meanings_of(t)
    if all(m.startswith("@") for m in ms) or not any(m.startswith("@") for m in ms):
        return is_marker(t)
    # Only the language's own matrix column shows a word working as a marker.
    grammar = [e.meaning for e in t.entries if e.meaning.startswith("@") and e.source == "column"]
    if not grammar:
        return is_marker(t)
    side = sides.get(grammar[0], default)
    if side == "after":
        return last is not None and i > 0 and words[i - 1] is last[0]
    if side == "before":
        nxt = words[i + 1] if i + 1 < len(words) else None
        return nxt is not None and not nxt.affix and not is_marker(nxt)
    return False


def _clause(tokens: list[Token], default: str | None, sides: dict) -> Clause:
    phrases: list[tuple[Token, list[Token]]] = []
    features: list[str] = []
    waiting: list[Token] = []    # prefixes and "before" markers for the next head
    last = None                  # the phrase the previous word joined, if any

    words = [t for t in tokens if t.kind in ("word", "number")]
    for i, t in enumerate(words):
        if t.affix == "prefix":
            waiting.append(t)
            last = None
        elif t.affix == "suffix" and phrases:
            phrases[-1][1].append(t)
            last = phrases[-1]
        elif t.kind == "word" and _acts_as_marker(t, words, i, default, sides, last):
            role = _role(t)
            side = sides.get(role, default)
            if side == "before":
                waiting.append(t)
                last = None
            elif side == "after" and last is not None:
                last[1].append(t)
            else:
                features.append(role)
                last = None
        else:
            phrases.append((t, waiting))
            waiting = []
            last = phrases[-1]
    features += [meaning_of(t) for t in waiting]
    if any(t.kind == "punct" and t.text in QUESTION for t in tokens) and "@question" not in features:
        features.append("@question")
    return Clause(
        tuple(tokens),
        tuple(Phrase(head, tuple(ms)) for head, ms in phrases),
        tuple(features),
    )


def parse(tokens: list[Token], language: str, *, root=None) -> list[Clause]:
    """Clauses for Analyze's tokens of a squirrel-lang-data language."""
    default, sides = _sides(language, root)
    clauses, current = [], []
    for t in tokens:
        current.append(t)
        if t.kind == "punct" and t.text in CLAUSE_END:
            clauses.append(_clause(current, default, sides))
            current = []
    if any(t.kind in ("word", "number") for t in current):
        clauses.append(_clause(current, default, sides))
    elif current and clauses:
        last = clauses.pop()
        clauses.append(Clause(last.tokens + tuple(current), last.phrases, last.features))
    return clauses
