"""The translation pipeline, one stage per module (roadmap Phase 1):
analyze, parse, interlingua, transfer and generate, rank.

run() chains them for a pair of squirrel-lang-data languages and returns a
Translation, the same type translate_full() returns. translate() and
translate_full() call it with engine="pipeline".
"""

from ..lexicon import available, lexicon
from ..result import Step, Translation, UnsupportedLanguage
from .analyze import analyze
from .generate import generate
from .interlingua import interlingua
from .parse import parse
from .rank import rank


def languages(root=None) -> list[str]:
    """Languages the pipeline can read and write: every language the data
    has a word list or a meaning-matrix column for, and English."""
    return available(root)


def run(source: str, from_lang: str, to_lang: str, *, root=None) -> Translation:
    """Translate between two squirrel-lang-data languages, clause by clause.

    text is each clause's best candidate. alternatives swap one clause's
    best for its next candidates. The breakdown has one Step per clause,
    whose why is Rank's note. unknown lists source words the data has no
    meaning for, and words the target has no word for. confidence is the
    mean of the best scores. Every pair is alpha.
    """
    supported = languages(root)
    for lang in (from_lang, to_lang):
        if lang not in supported:
            raise UnsupportedLanguage(lang, supported)
    text = source.strip()
    if from_lang == to_lang or not text:
        return Translation(text, confidence=1.0 if text else 0.0, from_lang=from_lang, to_lang=to_lang)

    sep = "" if to_lang != "english" and not lexicon(to_lang, root).spaced else " "
    lex = lexicon(from_lang, root)
    picks, steps, unknown = [], [], []
    for clause in parse(analyze(text, from_lang, lex=lex), from_lang, root=root):
        said = "".join(t.text for t in clause.tokens).strip()
        if not clause.phrases:
            continue
        il = interlingua(clause, from_lang, root=root)
        ranked = rank(generate(il, to_lang, root=root), il, from_lang, root=root)
        if not ranked:
            continue
        picks.append(ranked)
        steps.append(Step(said, ranked[0].text, ranked[0].note))
        unknown += [*il.unknown, *ranked[0].candidate.missing]

    best = [r[0].text for r in picks]
    alternatives = []
    for i, ranked in enumerate(picks):
        for other in ranked[1:]:
            alternatives.append(sep.join(best[:i] + [other.text] + best[i + 1:]))
    confidence = sum(r[0].score for r in picks) / len(picks) if picks else 0.0
    return Translation(
        sep.join(best), tuple(dict.fromkeys(alternatives)), tuple(steps),
        tuple(dict.fromkeys(unknown)), round(confidence, 3), True, from_lang, to_lang,
    )
