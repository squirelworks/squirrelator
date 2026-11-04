"""Interlingua: map a parsed clause to language-neutral meaning units.

Each phrase becomes a Unit: the meaning unit its head carries (from the
data, never guessed) and the roles its markers give it. Where a marker can
carry more than one role (Japanese で is @place or @means), the role the
meaning matrix most often pairs with that content meaning wins, and the
others are kept as alternatives.

The clause is then matched against the rows of the meaning matrix. A row
matches when it has every content meaning the clause has, and the only
meanings it adds are ones the source language leaves unsaid in that row
(Japanese drops "I"). A word the row's own wording uses may carry none of
the row's meanings: "is" in "Where is the station?" reads as exist on its
own, and "am" in "I am a student." is no word in the data, but both are
how English says those rows. Those are returned as implied units, so a later stage
can say "I" in English without the engine inventing it.
"""

from dataclasses import dataclass

from ..matrix import Matrix, matrix
from .parse import Clause, Phrase, meanings_of


@dataclass(frozen=True)
class Unit:
    meaning: str                       # "" when the data gives the word no meaning unit
    text: str                          # the source words, or "" for an implied unit
    roles: tuple[str, ...] = ()        # chosen grammar meanings, markers first
    alternatives: tuple[str, ...] = () # other meanings the head word can carry
    role_alternatives: tuple[tuple[str, ...], ...] = ()
    implied: bool = False
    also: tuple[str, ...] = ()         # more content meanings in one word (몰라요 = not + know)

    @property
    def meanings(self) -> tuple[str, ...]:
        return ((self.meaning,) if self.meaning else ()) + self.also


@dataclass(frozen=True)
class Interlingua:
    units: tuple[Unit, ...]
    features: tuple[str, ...]          # clause-wide grammar meanings
    matches: tuple[str, ...]           # matrix rows with exactly these meanings
    unknown: tuple[str, ...]           # source words with no meaning unit
    language: str = ""                 # the source language

    @property
    def meanings(self) -> tuple[str, ...]:
        return tuple(m for u in self.units for m in u.meanings)


def _choose(options: tuple[str, ...], content: str, mx: Matrix) -> tuple[str, tuple[str, ...]]:
    """The option the matrix pairs most often with content; ties keep data order."""
    ranked = sorted(options, key=lambda g: -mx.marker_weight(content, g))
    return ranked[0], tuple(ranked[1:])


def _unit(phrase: Phrase, mx: Matrix) -> Unit:
    # The data joins meanings one word carries with "+": "meet+@past",
    # "not+know". Content parts are meanings; "@" parts are roles.
    options = [m for m in meanings_of(phrase.head) if not m.startswith("@")]
    parts = options[0].split("+") if options else []
    content = [p for p in parts if not p.startswith("@")]
    meaning = content[0] if content else ""
    roles, alts = [p for p in parts if p.startswith("@")], []
    for options in phrase.roles:
        if not options:
            continue
        chosen, others = _choose(options, meaning, mx)
        roles.append(chosen)
        alts.append(others)
    return Unit(meaning, phrase.head.text, tuple(roles), tuple(options[1:]), tuple(alts),
                also=tuple(content[1:]))


def _wording(mx: Matrix, row_id: str, language: str) -> str:
    """How the source language writes a row, as " "-padded folded text:
    the English sentences for English, the column's tokens otherwise."""
    if language == "english":
        texts = (mx.rows[row_id].en, *mx.rows[row_id].also)
    else:
        rendering = mx.columns.get(language, {}).get(row_id)
        texts = (" ".join(t.strip("-") for t, _, _ in rendering.tokens),) if rendering else ()
    words = " ".join(texts).casefold()
    return " " + "".join(c if c.isalnum() or c in "'’" else " " for c in words) + " "


def _row_reading(mx: Matrix, row_id: str, language: str, text: str) -> list[str]:
    """The content meanings the language's column gives text in this row."""
    rendering = mx.columns.get(language, {}).get(row_id) if language != "english" else None
    return [m for t, _, ms in (rendering.tokens if rendering else ()) if t.strip("-") == text
            for m in ms.split("+") if not m.startswith("@")]


def _in(text: str, wording: str) -> bool:
    return f" {text.casefold()} " in wording


def interlingua(clause: Clause, language: str, *, root=None) -> Interlingua:
    """Meaning units, roles and matching matrix rows for one parsed clause."""
    mx = matrix(root)
    units = [_unit(p, mx) for p in clause.phrases]
    have = [m for u in units for m in u.meanings]

    found = []
    if units:
        for row in mx.rows.values():
            wording = _wording(mx, row.id, language)
            # A word the row's own wording has may carry no meaning of the
            # row: English "is" in "Where is the station?" is not exist.
            # Every other word must carry one of the row's meanings.
            free = [u for u in units if _in(u.text, wording)]
            needed = [m for u in units if u not in free for m in u.meanings]
            if any(not u.meaning for u in units if u not in free):
                continue
            if not set(needed) <= set(row.meanings):
                continue
            # A word the row's column writes reads as the row reads it: 家 is
            # home in going-home even when the word list gives house first.
            read = have + [m for u in free for m in _row_reading(mx, row.id, language, u.text)]
            if not set(row.meanings) & set(read):
                continue
            extra = [m for m in row.meanings if m not in read]
            unsaid = row.implied.get(language, ())
            if all(m in unsaid for m in extra):
                ignored = {u.text for u in free if not set(u.meanings) & set(row.meanings)}
                found.append((len(free), row.id, extra, ignored))
    # Rows whose wording has more of the clause's words come first: "How
    # much is it?" is how-much-is-it before how-much-this. Ties keep data order.
    found.sort(key=lambda f: -f[0])
    matches = tuple(f[1] for f in found)
    implied, explained = (found[0][2], found[0][3]) if found else (None, set())
    unknown = tuple(u.text for u in units if not u.meaning and u.text not in explained)
    implied_units = tuple(Unit(m, "", implied=True) for m in implied or ())
    return Interlingua(implied_units + tuple(units), clause.features, matches, unknown, language)
