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

For a target whose nouns change form by case (Latin), Agree picks each
word's form first: the case its role takes, the agreement of adjectives
and the person of the verb (see agree.py).

Implied units (the "I" Japanese leaves unsaid) are written in the words
candidate only when the target has a word for them.
"""

from dataclasses import dataclass

from ..inflections import inflections
from ..lexicon import language_meta, lexicon
from ..matrix import Matrix, matrix
from .agree import agree, pick_form
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


def _word(mx: Matrix, target: str, meaning: str, root=None) -> tuple[str, str] | None:
    if target == ENGLISH:
        words = mx.english.get(meaning, ())
        if meaning.startswith("@"):
            # Only markers English sentences in the matrix really use: "to",
            # "by", but not the "as for" that glosses a topic particle.
            words = tuple(w for w in words if _english_uses(mx, w))
        return (words[0], "") if words else None
    return mx.word(target, meaning) or _table_word(target, meaning, root)


def _table_word(target: str, meaning: str, root) -> tuple[str, str] | None:
    """A word the target's column never uses, from its inflection tables:
    the dictionary form of the first word carrying the meaning (Latin nāvis
    for ship, though no Latin matrix row has a ship)."""
    if meaning.startswith("@"):
        return None
    for word in inflections(target, root):
        form = word.form("dictionary")
        if word.meaning == meaning and form:
            return form.text, form.reading
    return None


def _english_uses(mx: Matrix, phrase: str) -> bool:
    needle = f" {phrase.casefold()} "
    return any(needle in f" {text.casefold().strip('.?!')} "
               for row in mx.rows.values() for text in (row.en, *row.also))


def _inflect(found: tuple[str, str], meaning: str, wanted: set[str], target: str, root) -> tuple[str, str]:
    """The form of found that carries the grammar the unit wants. The form
    the column usually writes sets the register: 行きます is polite, so
    @past gives 行きました, not 行った. Without a table, found stays."""
    for word in inflections(target, root):
        usual = next((f for f in word.forms if word.meaning == meaning and f.text == found[0]), None)
        if not usual:
            continue
        wanted = wanted & {x for f in word.forms for x in f.features}
        if not wanted:
            return found

        def fit(form):
            return (len(form.features & wanted) * 2 + len(form.features & usual.features)
                    - len(form.features - wanted - usual.features))
        best = max(word.forms, key=fit)
        return best.text, best.reading
    return found


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


def _capitalized(mx: Matrix, target: str) -> bool:
    """Whether the target's matrix column starts every sentence with a
    capital letter (Latin Discipulus sum.)."""
    firsts = [r.tokens[0][0] for r in mx.columns.get(target, {}).values() if r.tokens]
    cased = [t for t in firsts if t[:1].lower() != t[:1].upper()]
    return bool(cased) and all(t[0].isupper() for t in cased)


def _uncapped(mx: Matrix, target: str, found: tuple[str, str]) -> tuple[str, str]:
    """A word the column only ever writes first in a sentence (Ad scholam
    eō) with its capital taken off, when the column capitalizes sentences."""
    text = found[0]
    if not text[:1].isupper() or not _capitalized(mx, target):
        return found
    places = [i for r in mx.columns.get(target, {}).values() for i, t in enumerate(r.tokens) if t[0] == text]
    if places and all(i == 0 for i in places):
        return text[0].lower() + text[1:], found[1]
    return found


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

    # Case, agreement and person, for a target whose words change by case.
    firsts = [(_word(mx, target, u.meanings[0], root) or ("", ""))[0] if u.meanings else "" for u in il.units]
    plan = agree(il, target, firsts, root=root)
    by_unit = {id(u): i for i, u in enumerate(il.units)}

    units = _in_target_order(units, il, plan, target, root)

    pairs, missing, dropped = [], [], []
    for unit in units:
        k = by_unit[id(unit)]
        if k in plan.silent:
            continue  # the verb's ending says it (Dormiō, not Ego dormiō)
        words = []
        for n, meaning in enumerate(_meanings_for(unit, mx, target, root)):
            found = _word(mx, target, meaning, root)
            if found and n == 0 and plan.words[k] is not None:
                form = pick_form(plan.words[k], plan.wanted[k])
                words.append((form.text, form.reading))
            elif found:
                found = _inflect(found, meaning, set(unit.roles), target, root)
                words.append(_uncapped(mx, target, found) if any(plan.words) else found)
            elif not unit.implied:
                words.append((f"[{unit.text}]", ""))
                missing.append(unit.text)
        if not unit.meanings and not unit.implied:
            words.append((f"[{unit.text}]", ""))
            missing.append(unit.text)
        if not words:
            continue
        before, after = [], []
        table = [plan.words[k]] if plan.words[k] is not None else [
            w for w in inflections(target, root) if w.meaning in unit.meanings]
        roles = plan.roles[k] if plan.roles else unit.roles
        inflected = {r for r in roles if words and k not in plan.unformed
                     and any(r in f.features for w in table for f in w.forms)}
        for role in roles:
            if role in inflected:
                continue  # the verb form carries it
            found = _word(mx, target, role, root)
            if not found and role in plan.carried:
                continue  # the case ending says it (aquam is the object)
            if not found:
                dropped.append(role)
            else:
                found = _uncapped(mx, target, found) if any(plan.words) else found
                (before if placement(role) == "before" else after).append(found)
        pairs += before + words + after
    question = "@question" in il.features
    for feature in il.features:
        found = _word(mx, target, feature, root)
        if found:
            pairs = [found] + pairs if placement(feature) == "before" else pairs + [found]
    spaced = target == ENGLISH or lexicon(target, root).spaced
    text = render([t for t, _ in pairs], " " if spaced else "", _end(mx, target, question))
    if text and (target == ENGLISH or (plan.words and any(plan.words) and _capitalized(mx, target))):
        text = text[0].upper() + text[1:]
    reading = "" if target == ENGLISH else _reading(pairs)
    return Candidate(text, reading, "words", missing=tuple(missing), dropped=tuple(dict.fromkeys(dropped)))


def _meanings_for(unit, mx: Matrix, target: str, root) -> tuple[str, ...]:
    """The unit's meanings, but when the target has no word for the first
    and has one for another meaning the source word can carry, that one
    (English not is none or not; Klingon has -be' for not)."""
    meanings = unit.meanings
    if not meanings or _word(mx, target, meanings[0], root):
        return meanings
    for alt in unit.alternatives:
        content = [m for m in alt.split("+") if not m.startswith("@")]
        if content and _word(mx, target, content[0], root):
            return (content[0],) + meanings[1:]
    return meanings


def _in_target_order(units, il: Interlingua, plan, target: str, root) -> list:
    """For a target whose words don't show subject and object by case,
    the subject, object and verb in the order its meta.json "order" gives
    (Klingon OVS: Duj legh HoD). Other words keep their places."""
    order = language_meta(target, root).get("order", "")
    if not plan.slots or not order:
        return units
    placed = {id(il.units[i]): slot for slot, i in plan.slots.items()}
    where = [n for n, u in enumerate(units) if id(u) in placed]
    wanted = sorted((units[n] for n in where), key=lambda u: order.index(placed[id(u)]))
    out = list(units)
    for n, u in zip(where, wanted):
        out[n] = u
    return out


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
