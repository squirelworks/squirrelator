"""What the GUI's menus offer and how it shows a result, kept apart from
tkinter so it can be tested anywhere.

There are two engines. "Rules" is the rule-based translator for code and a
few phrases. "Pipeline (alpha)" translates between human languages from
squirrel-lang-data; a result drops the alpha badge when that pair clears
the coverage bar (#26). "Auto", the default as in translate(), uses the
pipeline for sentences between English, Latin and Klingon, Rules for the
other pairs Rules supports, and the pipeline for the rest. All three are
always in the menu: alpha labels a feature, it never hides one.
"""

from dataclasses import dataclass

from .features import Settings
from .result import Translation
from .translator import SUPPORTED, _engine_for, _pipeline_first, translate, translate_full

AUTO = "Auto"
RULES = "Rules"
PIPELINE = "Pipeline (alpha)"
ENGINES = (AUTO, RULES, PIPELINE)
ENGINE_IDS = {AUTO: "auto", RULES: "rules", PIPELINE: "pipeline"}

# The rules engine's languages: modern and popular, then older and legacy,
# then joke languages, A to Z inside each group, as AGENTS.md asks. The
# human languages it knows come first, A to Z, then pseudocode.
_RULES_ORDER = [
    "english", "klingon", "latin", "pseudocode",
    "javascript", "python", "shell", "sql",
    "quickbasic", "z80",
    "brainfood", "lolcode",
]


def _pipeline_languages() -> list[str]:
    from .pipeline import languages
    try:
        return languages()
    except Exception:
        return []


def _filter_langs(langs: list[str], settings: Settings | None) -> list[str]:
    """Drop languages whose feature switch is off (joke / older code groups)."""
    if settings is None:
        return langs
    return [lang for lang in langs if settings.allows_language(lang)]


def languages_for(engine: str, settings: Settings | None = None) -> list[str]:
    """The From/To menu entries for an engine (a label from ENGINES). Auto
    offers both engines' languages: human languages A to Z, then
    pseudocode and the programming languages in the rules order. Pass
    Settings to hide languages whose features.json switch is off."""
    rules = _filter_langs([lang for lang in _RULES_ORDER if lang in SUPPORTED], settings)
    if engine == PIPELINE:
        return _filter_langs(_pipeline_languages(), settings)
    if engine == AUTO:
        human = sorted(set(_pipeline_languages()) | {"english", "klingon", "latin"})
        human = _filter_langs(human, settings)
        return human + [lang for lang in rules if lang not in human]
    return rules


def runs_pipeline(engine: str, from_lang: str, to_lang: str) -> bool:
    """Whether the engine chosen in the menu sends this pair to the
    pipeline, so the GUI shows the pipeline's fuller result."""
    return _engine_for(ENGINE_IDS[engine], from_lang, to_lang) == "pipeline"


def format_result(t: Translation) -> str:
    """The result pane's text: the translation, then what a learner should
    know about it: words the data doesn't cover, how sure the engine is, and
    a second opinion when Auto asks for one. Other wordings live in the
    Alternatives list under the result."""
    parts = [t.text]
    if t.unknown:
        parts.append("Not in the data yet: " + ", ".join(t.unknown))
    if t.breakdown and any(s.why for s in t.breakdown):
        parts.append("Why:\n" + "\n".join(f"  {s.source}\n    {s.why}" for s in t.breakdown))
    if t.alpha:
        parts.append(f"Alpha. Confidence {round(t.confidence * 100)}%.")
    if t.second_opinion:
        parts.append(_second_opinion(t.second_opinion))
    return "\n\n".join(parts)


def format_rules_result(t: Translation) -> str:
    """The result pane's text for a rules result: the rules text as before,
    plus the pipeline's second opinion when there is one (a code
    instruction such as "print hello" to Latin or Klingon)."""
    return "\n\n".join([t.text] + ([_second_opinion(t.second_opinion)] if t.second_opinion else []))


def pipeline_label(alpha: bool = True) -> str:
    """Engine name shown for a Pipeline result: alpha only while the pair
    is still under the coverage bar (#26). The Engine menu keeps PIPELINE
    so a feature under test stays visible; the result text matches the pair."""
    return PIPELINE if alpha else "Pipeline"


def _second_opinion(o: Translation) -> str:
    name = RULES if o.engine == "rules" else pipeline_label(o.alpha)
    lines = [f"Second opinion from {name}, confidence {round(o.confidence * 100)}%:", f"  {o.text}"]
    lines += [f"  Also: {a}" for a in o.alternatives]
    if o.unknown:
        lines.append("  Not in the data yet: " + ", ".join(o.unknown))
    return "\n".join(lines)


@dataclass(frozen=True)
class TranslateView:
    """What the translate screen shows: main result text, primary alternatives,
    and which engine label to show in the status line."""

    result: str
    alternatives: tuple[str, ...]
    engine: str


def _translate_view(source: str, from_lang: str, to_lang: str, engine: str) -> TranslateView:
    if engine == AUTO and _pipeline_first(from_lang, to_lang):
        t = translate_full(source, from_lang, to_lang)
        if t.engine == "pipeline":
            return TranslateView(format_result(t), t.alternatives, pipeline_label(t.alpha))
        return TranslateView(format_rules_result(t), t.alternatives, RULES)
    if runs_pipeline(engine, from_lang, to_lang):
        t = translate_full(source, from_lang, to_lang, engine=ENGINE_IDS[engine])
        return TranslateView(format_result(t), t.alternatives, pipeline_label(t.alpha))
    if engine == AUTO and from_lang in SUPPORTED and to_lang in SUPPORTED:
        t = translate_full(source, from_lang, to_lang)
        return TranslateView(format_rules_result(t), t.alternatives, RULES)
    text = translate(source, from_lang, to_lang, engine=ENGINE_IDS[engine])
    return TranslateView(text, (), RULES)


def translate_view(source: str, from_lang: str, to_lang: str, engine: str = AUTO) -> TranslateView:
    """Structured translate screen output for the Tk GUI and web twin."""
    return _translate_view(source, from_lang, to_lang, engine)


def display(source: str, from_lang: str, to_lang: str, engine: str = AUTO) -> tuple[str, str]:
    """What an app shows for a translation, and which engine (a label from
    ENGINES) made it. Every app calls this, so the desktop GUI and the
    phone show the same thing: a pipeline pair's full result, a rules pair's
    plain text, and under Auto, for English, Latin and Klingon, whichever
    engine understood the source better, with the other's second opinion."""
    view = _translate_view(source, from_lang, to_lang, engine)
    return view.result, view.engine
