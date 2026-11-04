"""Transfer and generate: meaning units to sentences in the target language.

Two ways, both read from the data and neither invents a word:

- matrix: the clause matched rows of the meaning matrix, and the target
  language's column renders those rows. This is the data's own sentence,
  so it is the best candidate when the row really says the same thing.
  English rows come from sentences.jsonl ("en" and "also").
- words: word by word. Each meaning becomes the word the target column
  most often uses for it alone, and each role the marker the column uses
  for it, placed before or after its word as the target's meta.json
  "markers" says. Words go where the target's matrix rows usually put
  their meaning (Japanese verbs last). This is a rough gloss for a
  learner, not a sentence; the Rank stage orders it below matrix
  candidates. A meaning the target has no word for stays as the source word
  in brackets and is listed under missing. A role the target has no marker
  for (English has no topic particle) is left out and listed under dropped.

Implied units (the "I" Japanese leaves unsaid) are written in the words
candidate only when the target has a word for them.
"""

from dataclasses import dataclass

from ..lexicon import language_meta, lexicon
from ..matrix import Matrix, matrix
from .interlingua import Interlingua

ENGLISH = "english"


@dataclass(frozen=True)
class Candidate:
    text: str
    reading: str                     # the target's romanization or kana, "" for English
    method: str                      # "matrix" or "words"
    row: str = ""                    # the matrix row a matrix candidate renders
    missing: tuple[str, ...] = ()    # source words kept as [word]: no target word
    dropped: tuple[str, ...] = ()    # roles the target has no marker for


def render(tokens, sep: str, end: str = "") -> str:
    """Join column-style tokens. A leading "-" glues a token to the one
    before, a trailing "-" to the one after (Korean 저 -는 is 저는)."""
    out, glue = "", True
    for text in tokens:
        lead, trail = text.startswith("-") and len(text) > 1, text.endswith("-") and len(text) > 1
        word = text[1 if lead else 0:len(text) - 1 if trail else len(text)]
        out += ("" if glue or lead else sep) + word
        glue = trail
    return out + end


def _reading(pairs) -> str:
    return " ".join(r or t.strip("-") for t, r in pairs)


def _word(mx: Matrix, target: str, meaning: str) -> tuple[str, str] | None:
    if target == ENGLISH:
        words = mx.english.get(meaning, ())
        if meaning.startswith("@"):
            # Only markers English sentences in the matrix really use: "to",
            # "by", but not the "as for" that glosses a topic particle.
            words = tuple(w for w in words if _english_uses(mx, w))
        return (words[0], "") if words else None
    return mx.word(target, meaning)


def _english_uses(mx: Matrix, phrase: str) -> bool:
    needle = f" {phrase.casefold()} "
    return any(needle in f" {text.casefold().strip('.?!')} "
               for row in mx.rows.values() for text in (row.en, *row.also))


def _end(mx: Matrix, target: str, question: bool) -> str:
    """Closing punctuation as the target column writes it for a question or
    a statement, taken from the rows whose English ends the same way."""
    mark = "?" if question else "."
    if target == ENGLISH:
        return mark
    for row_id, rendering in mx.columns.get(target, {}).items():
        if mx.rows[row_id].en.endswith(mark):
            return rendering.end
    return ""


def _from_matrix(il: Interlingua, target: str, mx: Matrix) -> list[Candidate]:
    out = []
    for row_id in il.matches:
        row = mx.rows[row_id]
        if target == ENGLISH:
            out += [Candidate(text, "", "matrix", row_id) for text in (row.en, *row.also) if text]
        elif rendering := mx.columns.get(target, {}).get(row_id):
            texts = [t for t, _, _ in rendering.tokens]
            out.append(Candidate(render(texts, rendering.sep, rendering.end),
                                 _reading((t, r) for t, r, _ in rendering.tokens), "matrix", row_id))
    return out


def _from_words(il: Interlingua, target: str, mx: Matrix, root) -> Candidate:
    markers = language_meta(target, root).get("markers", {})

    def placement(role: str) -> str:
        return markers.get(role, markers.get("default", "after"))

    # Units go where the target usually puts their meaning (Japanese verbs
    # last). A meaning the target's rows never place keeps its source
    # neighbour's position, so the sort is stable for it.
    order, positions, last = mx.order.get(target, {}), [], 0.5
    for unit in il.units:
        last = next((order[m] for m in unit.meanings if m in order), last)
        positions.append(last)
    units = [u for _, u in sorted(zip(positions, il.units), key=lambda p: p[0])]

    pairs, missing, dropped = [], [], []
    for unit in units:
        words = []
        for meaning in unit.meanings:
            found = _word(mx, target, meaning)
            if found:
                words.append(found)
            elif not unit.implied:
                words.append((f"[{unit.text}]", ""))
                missing.append(unit.text)
        if not unit.meanings and not unit.implied:
            words.append((f"[{unit.text}]", ""))
            missing.append(unit.text)
        if not words:
            continue
        before, after = [], []
        for role in unit.roles:
            found = _word(mx, target, role)
            if not found:
                dropped.append(role)
            else:
                (before if placement(role) == "before" else after).append(found)
        pairs += before + words + after
    question = "@question" in il.features
    for feature in il.features:
        found = _word(mx, target, feature)
        if found:
            pairs = [found] + pairs if placement(feature) == "before" else pairs + [found]
    spaced = target == ENGLISH or lexicon(target, root).spaced
    text = render([t for t, _ in pairs], " " if spaced else "", _end(mx, target, question))
    if target == ENGLISH and text:
        text = text[0].upper() + text[1:]
    reading = "" if target == ENGLISH else _reading(pairs)
    return Candidate(text, reading, "words", missing=tuple(missing), dropped=tuple(dict.fromkeys(dropped)))


def generate(il: Interlingua, target: str, *, root=None) -> tuple[Candidate, ...]:
    """Candidate sentences in the target language for one clause: the matrix
    rows the clause matched, as the target writes them, then a word-by-word
    gloss. Duplicates are dropped; Rank orders what is left."""
    mx = matrix(root)
    out, seen = [], set()
    for c in [*_from_matrix(il, target, mx), _from_words(il, target, mx, root)]:
        if c.text and c.text not in seen:
            seen.add(c.text)
            out.append(c)
    return tuple(out)
