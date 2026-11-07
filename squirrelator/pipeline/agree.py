"""Agree: the grammar each word needs in a language whose words change form
by case, such as Latin.

Generate calls this before it writes a word-by-word gloss. It reads three
things from squirrel-lang-data and never guesses a form:

- languages/<target>/inflections.jsonl gives each word's forms, tagged with
  case (@accusative), number (@plural), gender (@feminine) and person
  (@first-person). A noun's forms all carry its own gender, and a personal
  pronoun's carry its person.
- languages/<target>/meta.json "cases" gives the case a word takes for each
  role (@object -> @accusative) and after a word with a content meaning
  (from -> @ablative, for ab and ex).
- languages/<source>/meta.json "order" (English SVO) tells the subject from
  the object when the source marks neither. A word after a copula (the verb
  the target's matrix column writes as @copula) is not an object: "This is
  a book" keeps book in the nominative.

Then nouns and pronouns take their case, adjectives take the case, number
and gender of the noun beside them, and the verb takes the person and number
of its subject. A target without "cases" is left as it was.
"""

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from ..data import data_dir
from ..inflections import Word, inflections
from ..lexicon import language_meta
from ..matrix import matrix
from .interlingua import Interlingua, Unit

TENSE = {"@present", "@past"}
GENDERS = {"@masculine", "@feminine", "@neuter"}
PERSONS = {"@first-person", "@second-person", "@third-person"}
PLURAL = "@plural"
SUBJECT, OBJECT = "@subject", "@object"


@dataclass
class Plan:
    """What Agree decided for one clause, one entry per unit."""
    wanted: list[set[str]]
    words: list[Word | None]
    carried: set[str] = field(default_factory=set)   # roles a case says, so no marker is missing
    silent: set[int] = field(default_factory=set)    # subject pronouns the verb's ending says
    roles: list[tuple[str, ...]] | None = None       # each unit's roles, after moving
    unformed: set[int] = field(default_factory=set)  # nouns whose role a case and marker say, not a form
    slots: dict[str, int] = field(default_factory=dict)  # "S", "O", "V" -> unit, for a target without cases


def _kind(word: Word | None, case_features: set[str]) -> str:
    if word is None:
        return ""
    features = {x for f in word.forms for x in f.features}
    if features & TENSE:
        return "verb"
    if len(features & GENDERS) > 1 and not features & PERSONS:
        return "adjective"
    if features & case_features:
        return "nominal"
    return ""


def _inherent(word: Word) -> set[str]:
    """Features every form of the word has: a noun's gender, a pronoun's person."""
    sets = [set(f.features) for f in word.forms]
    return set.intersection(*sets) if sets else set()


def _cited_person(unit: Unit, language: str, root) -> set[str]:
    """The person every inflection of this spelling shares.

    A bare Klingon jatlh is third person in the table, but the word list
    writes that spelling with no person, so the unit's roles don't say who
    acts. When every form spelled this way shares one person, that is what
    the source said."""
    if not unit.text or not language or not unit.meanings:
        return set()
    found = []
    for word in inflections(language, root):
        if word.meaning not in unit.meanings:
            continue
        forms = [f for f in word.forms if f.text.casefold() == unit.text.casefold()]
        if not forms:
            continue
        shared = set.intersection(*(set(f.features) for f in forms)) & PERSONS
        if len(shared) == 1:
            found.append(shared)
    return found[0] if len(found) == 1 else set()


def pick_form(word: Word, wanted: set[str]):
    """The form carrying most of what is wanted and least that isn't."""
    inherent = _inherent(word)

    def fit(form):
        return (len(form.features & wanted), -len(form.features - wanted - inherent), form.name == "dictionary")
    return max(word.forms, key=fit)


@lru_cache(maxsize=None)
def _copulas(target: str, root: Path) -> frozenset[str]:
    """Forms the target's matrix column writes as @copula (Latin est, sum)."""
    out = set()
    for rendering in matrix(root).columns.get(target, {}).values():
        for text, _, meaning in rendering.tokens:
            if "@copula" in meaning.split("+"):
                out.add(text.casefold())
    return frozenset(out)


def table_word(unit: Unit, meaning: str, found: str, target: str, root) -> Word | None:
    """The target's table entry for a meaning: the one with a form the unit's
    roles name (meus for i with @possessive), else the one holding the word
    the column uses (mihi is a form of ego), else the first."""
    words = [w for w in inflections(target, root) if w.meaning == meaning]
    if not words:
        return None
    for w in words:
        if set(unit.roles) & {x for f in w.forms for x in f.features}:
            return w
    for w in words:
        if any(f.text.casefold() == found.casefold() for f in w.forms):
            return w
    return words[0]


def _features(word: Word | None) -> set[str]:
    return {x for f in word.forms for x in f.features} if word else set()


def _marked(roles, word: Word | None, target: str, root) -> bool:
    """Whether a role the target says, by a marker or by the word's form,
    gives a word its part in the clause (DujDaq is in the ship). A role the
    target has no way to say (English the, for Klingon) doesn't."""
    mx = matrix(root)
    return any(r != PLURAL and (r in _features(word) or mx.word(target, r)) for r in roles)


def _by_person(il: Interlingua, target: str, words: list[Word | None], root) -> Plan | None:
    """Agreement for a target whose verbs show their subject and object in
    the verb's own form rather than by case (Klingon jIQong is I sleep,
    vIlegh is I see him). None when the target's verbs don't: its words
    then keep the forms the column writes.

    The subject and object come from the source's "order" (English SVO) or
    from the roles its markers give. The verb takes the subject's person
    and number, and @object when a third-person object is there. A subject
    pronoun the verb's form says is left out (jIQong, not jIH jIQong), and
    nouns take the number and roles their forms carry (puqpu', DujDaq).
    "slots" names the subject, object and verb for Generate to order."""
    units = il.units
    kinds = ["verb" if _features(w) & TENSE else ("nominal" if w is not None else "") for w in words]
    # Only verbs with a form for every person say who acts (Klingon jI-,
    # bI-, ma-); English marks only he, she and it (sees), so it keeps its
    # pronouns and the column's forms.
    verbs = [i for i, k in enumerate(kinds) if k == "verb" and PERSONS <= _features(words[i])]
    if not verbs:
        return None
    v = verbs[0]
    roles = [tuple(u.roles) for u in units]
    wanted = [set(r) for r in roles]
    nominals = [i for i, k in enumerate(kinds) if k == "nominal" and not units[i].implied]
    subject = next((i for i in nominals if SUBJECT in roles[i]), None)
    obj = next((i for i in nominals if OBJECT in roles[i]), None)
    source = language_meta(il.language, root) if il.language else {}
    order = source.get("order", "")
    if order:
        s_before, o_before = order.index("S") < order.index("V"), order.index("O") < order.index("V")
        for i in nominals:
            if i in (subject, obj) or _marked(roles[i], words[i], target, root):
                continue  # a word with a marker (in the ship) is neither
            before = i < v
            if s_before != o_before:
                role = SUBJECT if before == s_before else OBJECT
            else:
                same = [j for j in nominals if (j < v) == before]
                role = SUBJECT if (i == same[0]) == (order.index("S") < order.index("O")) else OBJECT
            if role == SUBJECT and subject is None:
                subject = i
            elif role == OBJECT and obj is None:
                obj = i
    if subject is None:
        # No word says the subject: an implied one (Japanese drops I) does.
        subject = next((i for i, u in enumerate(units) if u.implied and kinds[i] == "nominal"), None)

    verb_features = _features(words[v])
    if not wanted[v] & TENSE and "@command" not in wanted[v]:
        wanted[v].add("@present")
    silent = set()
    if subject is not None and "@command" not in wanted[v]:
        person = _inherent(words[subject]) & PERSONS
        wanted[v] |= person or {"@third-person"}
        if PLURAL in wanted[subject] or PLURAL in _inherent(words[subject]):
            wanted[v].add(PLURAL)
        if person:
            silent.add(subject)  # the verb's form says it
    elif subject is None and "@command" not in wanted[v]:
        cited = _cited_person(units[v], il.language, root)
        if cited:
            wanted[v] |= cited
        else:
            dictionary = words[v].form("dictionary")
            wanted[v] |= (dictionary.features - TENSE) if dictionary else set()
    if obj is not None and OBJECT in verb_features:
        # The forms with @object take a third-person object (vIlegh).
        if not _inherent(words[obj]) & (PERSONS - {"@third-person"}):
            wanted[v].add(OBJECT)
    if "@command" in wanted[v] and obj is not None and OBJECT in verb_features:
        wanted[v].add(OBJECT)
    slots = {k: i for k, i in (("S", subject), ("O", obj), ("V", v)) if i is not None}
    return Plan(wanted, words, set(), silent, list(roles), set(), slots)


def agree(il: Interlingua, target: str, found: list[str], *, root=None) -> Plan:
    """found holds, per unit, the word the target column uses for its first
    meaning ("" for none)."""
    units = il.units
    words = [table_word(u, u.meanings[0], f, target, root) if u.meanings else None
             for u, f in zip(units, found)]
    wanted = [set(u.roles) for u in units]
    cases = language_meta(target, root).get("cases") or {}
    if not cases:
        return _by_person(il, target, words, root) or Plan(
            wanted, [None] * len(units), roles=[u.roles for u in units])
    case_features = set(cases.values())
    kinds = [_kind(w, case_features) for w in words]
    source = language_meta(il.language, root) if il.language else {}
    side = (source.get("markers") or {}).get("default", "before")
    case: list[str | None] = [None] * len(units)
    carried = set()

    def has(word, feature):
        return word is not None and any(feature in f.features for f in word.forms)

    # English puts a preposition before the adjective ("in a big house"),
    # but the role belongs to the noun the adjective describes.
    roles = [list(u.roles) for u in units]
    described: set[int] = set()   # nouns an adjective describes
    unformed: set[int] = set()
    for i, k in enumerate(kinds):
        if k != "adjective":
            continue
        j = next((j for j in range(i + 1, len(units)) if kinds[j] in ("nominal", "verb")), None)
        if j is None or kinds[j] != "nominal":
            continue
        described.add(j)
        moving = [r for r in roles[i] if r in cases]
        roles[i] = [r for r in roles[i] if r not in moving]
        roles[j] = moving + [r for r in roles[j] if r not in moving]
    wanted = [set(r) for r in roles]

    # A role the word's own form carries (domī is at home) needs no case.
    for i, u in enumerate(units):
        for role in roles[i]:
            if role in cases and has(words[i], role) and i in described:
                # domī alone is at home, but an adjective needs a case to
                # agree with: in magnā domō.
                unformed.add(i)
                wanted[i].discard(role)
            if role in cases and (not has(words[i], role) or i in unformed):
                case[i] = case[i] or cases[role]
                carried.add(role)

    nominals = [i for i, k in enumerate(kinds) if k == "nominal"]
    alone: set[int] = set()   # adjectives a preposition governs directly
    # A content meaning that takes a case (from) gives it to the next word,
    # on the side the source writes its markers.
    for i, u in enumerate(units):
        for m in u.meanings:
            if m in cases:
                # A numeral or adjective standing alone (ab ūnō) takes it too.
                takers = [j for j, k in enumerate(kinds) if k in ("nominal", "adjective")]
                near = [j for j in takers if (j > i if side == "before" else j < i)]
                if near:
                    j = near[0] if side == "before" else near[-1]
                    if kinds[j] == "adjective":
                        # ex magnā domō: the case goes to the noun after it.
                        noun = next((n for n in range(j + 1, len(units)) if kinds[n] in ("nominal", "verb")), None)
                        if noun is not None and kinds[noun] == "nominal":
                            j = noun
                        else:
                            alone.add(j)
                    case[j] = case[j] or cases[m]

    verbs = [i for i, k in enumerate(kinds) if k == "verb"]
    order = source.get("order", "")
    subject = next((i for i in range(len(units)) if SUBJECT in roles[i]), None)
    if verbs and order and SUBJECT in cases:
        v = verbs[0]
        copula = "@copula" in units[v].roles or any(
            f.text.casefold() in _copulas(target, data_dir(root)) for f in words[v].forms)
        open_ = [i for i in nominals if case[i] is None and not units[i].implied
                 and not set(roles[i]) & set(cases)]
        s_before, o_before = order.index("S") < order.index("V"), order.index("O") < order.index("V")
        for i in open_:
            before = i < v
            if copula:
                role = SUBJECT
            elif s_before != o_before:
                role = SUBJECT if before == s_before else OBJECT
            else:
                same_side = [j for j in open_ if (j < v) == before]
                first_is_s = order.index("S") < order.index("O")
                role = SUBJECT if (i == same_side[0]) == first_is_s else OBJECT
            if role in cases:
                case[i] = cases[role]
                if role == SUBJECT and subject is None:
                    subject = i
    if subject is None:
        # A topic nothing else gives a case is the subject (友達は).
        subject = next((i for i in nominals if case[i] is None and "@topic" in units[i].roles), None)
        if subject is not None and SUBJECT in cases:
            case[subject] = cases[SUBJECT]
    if subject is None:
        # The source marks no subject, but the target's matrix leaves one
        # unsaid (Japanese drops I): it is the implied unit.
        subject = next((i for i, u in enumerate(units) if u.implied and kinds[i] == "nominal"), None)
    for i in nominals:
        if case[i]:
            wanted[i].add(case[i])

    # Adjectives take the case, number and gender of the noun beside them;
    # after a copula, of the subject.
    for i, k in enumerate(kinds):
        if k != "adjective":
            continue
        if i in alone:
            wanted[i].add(case[i])
            continue
        after_copula = verbs and i > verbs[0] and subject is not None and subject < verbs[0]
        near = [j for j in nominals if j > i][:1] or [j for j in nominals if j < i][-1:]
        j = subject if after_copula and not [n for n in nominals if n > i] else (near[0] if near else None)
        if j is None:
            continue
        noun = words[j]
        wanted[i] |= {x for x in wanted[j] if x in case_features or x == PLURAL}
        wanted[i] |= _inherent(noun) & GENDERS
        if not wanted[j] & case_features and SUBJECT in cases:
            wanted[i].add(cases[SUBJECT])

    # The verb takes its subject's person and number. With no subject, a
    # source form that already says who acts keeps that person (bare jatlh
    # is third person). Otherwise it keeps the target dictionary form's
    # person (Japanese leaves "I" unsaid: 飲みました is bibī).
    silent = set()
    for v in verbs[:1]:
        if not wanted[v] & TENSE and "@command" not in wanted[v]:
            wanted[v].add("@present")
        if subject is None:
            # A source form that already says who acts (bare jatlh is third
            # person) keeps that person. Otherwise the target's dictionary
            # form does (Japanese leaves "I" unsaid: 飲みました is bibī).
            cited = _cited_person(units[v], il.language, root)
            if cited:
                wanted[v] |= cited
            else:
                dictionary = words[v].form("dictionary")
                wanted[v] |= (dictionary.features - TENSE) if dictionary else set()
    if verbs and subject is not None:
        v, s = verbs[0], subject
        person = _inherent(words[s]) & PERSONS if words[s] else set()
        wanted[v] |= person or {"@third-person"}
        if PLURAL in wanted[s] or (words[s] and PLURAL in _inherent(words[s])):
            wanted[v].add(PLURAL)
        mx = matrix(root)
        unsaid = {m for row in mx.rows.values() for m in row.implied.get(target, ())}
        if person and set(units[s].meanings) & unsaid:
            silent.add(s)
    return Plan(wanted, words, carried, silent, [tuple(r) for r in roles], unformed)
