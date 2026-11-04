"""What the GUI's menus offer and how it shows a result, kept apart from
tkinter so it can be tested anywhere.

There are two engines. "Rules" is the rule-based translator for code and a
few phrases. "Pipeline (alpha)" translates between human languages from
squirrel-lang-data. "Auto", the default as in translate(), uses Rules for
every pair Rules supports and the pipeline for the rest. All three are
always in the menu: alpha labels a feature, it never hides one.
"""

from .result import Translation
from .translator import SUPPORTED, _engine_for

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


def languages_for(engine: str) -> list[str]:
    """The From/To menu entries for an engine (a label from ENGINES). Auto
    offers both engines' languages: human languages A to Z, then
    pseudocode and the programming languages in the rules order."""
    rules = [lang for lang in _RULES_ORDER if lang in SUPPORTED]
    if engine == PIPELINE:
        return _pipeline_languages()
    if engine == AUTO:
        human = sorted(set(_pipeline_languages()) | {"english", "klingon", "latin"})
        return human + [lang for lang in rules if lang not in human]
    return rules


def runs_pipeline(engine: str, from_lang: str, to_lang: str) -> bool:
    """Whether the engine chosen in the menu sends this pair to the
    pipeline, so the GUI shows the pipeline's fuller result."""
    return _engine_for(ENGINE_IDS[engine], from_lang, to_lang) == "pipeline"


def format_result(t: Translation) -> str:
    """The result pane's text: the translation, then what a learner should
    know about it: other wordings, words the data doesn't cover, and how
    sure the engine is. The GUI uses it for the pipeline; the rules engine
    keeps showing its plain text."""
    parts = [t.text]
    if t.alternatives:
        parts.append("Also:\n" + "\n".join(f"  {a}" for a in t.alternatives))
    if t.unknown:
        parts.append("Not in the data yet: " + ", ".join(t.unknown))
    if t.breakdown and any(s.why for s in t.breakdown):
        parts.append("Why:\n" + "\n".join(f"  {s.source}\n    {s.why}" for s in t.breakdown))
    if t.alpha:
        parts.append(f"Alpha. Confidence {round(t.confidence * 100)}%.")
    return "\n\n".join(parts)
