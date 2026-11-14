"""Pure helpers for the translate screen layout (Tk, web, and tests)."""

from dataclasses import dataclass

from .result import Step

_LABELS = {
    "brainfood": "brainFOOD",
    "javascript": "JavaScript",
    "lolcode": "LOLCODE",
    "pseudocode": "Pseudocode",
    "quickbasic": "QuickBASIC",
    "shell": "Shell",
    "sql": "SQL",
    "z80": "Z80 Assembly",
}


def language_label(lang_id: str) -> str:
    """A language id as people read it in the UI."""
    if not lang_id:
        return ""
    key = lang_id.lower()
    if key in _LABELS:
        return _LABELS[key]
    return lang_id.replace("_", " ").title()


def format_alternatives_lines(alternatives: tuple[str, ...] | list[str]) -> list[str]:
    """User-facing alternative wordings, one line each, for the Alternatives
    section under the result."""
    return [a for a in alternatives if a]


@dataclass(frozen=True)
class BreakdownRow:
    """One selectable row in the Breakdown view."""

    dictionary_form: str
    meaning_unit: str
    note: str

    @property
    def summary(self) -> str:
        """Short label for a list row."""
        return self.dictionary_form or self.meaning_unit or self.note


def format_breakdown_rows(breakdown: tuple[Step, ...] | list[Step]) -> list[BreakdownRow]:
    """Turn pipeline or rules breakdown steps into plain-language rows for the UI."""
    rows: list[BreakdownRow] = []
    for step in breakdown:
        if not (step.source or step.result or step.why):
            continue
        rows.append(BreakdownRow(step.source, step.result, step.why))
    return rows


def swap_translate_state(
    from_lang: str, to_lang: str, source: str, result: str
) -> tuple[str, str, str, str]:
    """Swap From/To. When the result pane has text, move it into the source
    pane and put the old source in the result pane so reverse translation is
    one click away."""
    new_from, new_to = to_lang, from_lang
    src, res = source or "", result or ""
    if res.strip():
        return new_from, new_to, res, src if src.strip() else ""
    return new_from, new_to, src, res