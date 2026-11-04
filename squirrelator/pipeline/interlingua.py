"""Interlingua: map a parsed clause to language-neutral meaning units.

Each phrase becomes a Unit: the meaning unit its head carries (from the
data, never guessed) and the roles its markers give it. Where a marker can
carry more than one role (Japanese で is @place or @means), the role the
meaning matrix most often pairs with that content meaning wins, and the
others are kept as alternatives.

The clause is then matched against the rows of the meaning matrix. A row
matches when it has every content meaning the clause has, and the only
meanings it adds are ones the source language leaves unsaid in that row
(Japanese drops "I"). Those are returned as implied units, so a later stage
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


def interlingua(clause: Clause, language: str, *, root=None) -> Interlingua:
    """Meaning units, roles and matching matrix rows for one parsed clause."""
    mx = matrix(root)
    units = [_unit(p, mx) for p in clause.phrases]
    have = [m for u in units for m in u.meanings]
    unknown = tuple(u.text for u in units if not u.meaning)

    matches, implied = [], None
    if have and not unknown:
        for row in mx.rows.values():
            if sorted(have) == sorted(m for m in row.meanings if m in have) and set(have) <= set(row.meanings):
                extra = [m for m in row.meanings if m not in have]
                unsaid = row.implied.get(language, ())
                if all(m in unsaid for m in extra):
                    matches.append(row.id)
                    if implied is None:
                        implied = extra
    implied_units = tuple(Unit(m, "", implied=True) for m in implied or ())
    return Interlingua(implied_units + tuple(units), clause.features, tuple(matches), unknown)
