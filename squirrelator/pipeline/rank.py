"""Rank: order Generate's candidates, best first, with a score and a note.

Scores are between 0 and 1 and only order candidates; they are not
probabilities.

- A matrix candidate is the data's own sentence, so it starts at 1. When
  the source language's column also renders that row, every grammar
  meaning the row has and the clause lacks, or the clause has and the row
  lacks (@past against a present-tense row), costs 0.25. Other English
  wordings of the same row come just after the first.
- A words candidate is a gloss, so it starts at 0.5, scaled by the share of
  the clause's words the target has a word for, less 0.05 for each marker
  it had to drop.

Ties keep Generate's order.
"""

from dataclasses import dataclass

from ..matrix import matrix
from .generate import Candidate
from .interlingua import Interlingua

MISMATCH = 0.25
WORDING = 0.01
GLOSS = 0.5
DROPPED = 0.05


@dataclass(frozen=True)
class Ranked:
    candidate: Candidate
    score: float
    note: str              # why it ranks where it does, in plain words

    @property
    def text(self) -> str:
        return self.candidate.text


def _grammar(il: Interlingua) -> set[str]:
    return {r for u in il.units for r in u.roles} | set(il.features)


def _row_grammar(tokens) -> set[str]:
    return {m for _, _, ms in tokens for m in ms.split("+") if m.startswith("@")}


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def rank(candidates, il: Interlingua, source: str, *, root=None) -> tuple[Ranked, ...]:
    """Candidates for one clause, best first."""
    mx = matrix(root)
    have = _grammar(il)
    words = sum(1 for u in il.units if not u.implied) or 1
    out, wordings = [], {}
    for c in candidates:
        if c.method == "matrix":
            n = wordings[c.row] = wordings.get(c.row, -1) + 1
            score, note = 1.0 - n * WORDING, "A sentence from the meaning matrix."
            rendering = mx.columns.get(source, {}).get(c.row)
            if rendering:
                off = sorted(have ^ _row_grammar(rendering.tokens))
                if off:
                    score -= MISMATCH * len(off)
                    note = f"A sentence from the meaning matrix, but its grammar differs: {', '.join(off)}."
        else:
            covered = 1 - len(c.missing) / words
            score = GLOSS * covered - DROPPED * len(c.dropped)
            gaps = []
            if c.missing:
                gaps.append(f"{_plural(len(c.missing), 'word')} with no translation in the data")
            if c.dropped:
                gaps.append(f"{_plural(len(c.dropped), 'marker')} left out")
            note = "Word by word" + (f", {' and '.join(gaps)}." if gaps else ".")
        out.append(Ranked(c, round(max(score, 0.0), 3), note))
    return tuple(sorted(out, key=lambda r: -r.score))
