"""Pure helpers for the translate screen layout (Tk, web, and tests)."""

import re
from dataclasses import dataclass
from typing import Literal

from .result import Step

_CODE_LANGS = frozenset({
    "python", "javascript", "quickbasic", "brainfood", "lolcode",
    "z80", "sql", "shell",
})

_BRACKETS = re.compile(r"\[[^\]]+\]")

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

CODE_PICKER_GROUP = "Code"

# Rules-engine languages in menu order (mirrors menus._RULES_ORDER for the web twin).
RULES_LANG_ORDER: tuple[str, ...] = (
    "english", "klingon", "latin", "pseudocode",
    "javascript", "python", "shell", "sql",
    "quickbasic", "z80",
    "brainfood", "lolcode",
)


@dataclass(frozen=True)
class PickerEntry:
    """One row in a From/To picker: a language id or a non-selectable group header."""

    kind: Literal["language", "header"]
    value: str


def is_natural_language(lang_id: str) -> bool:
    """True for human languages and pseudocode; false for programming targets."""
    if not lang_id:
        return False
    return lang_id.lower() not in _CODE_LANGS


@dataclass(frozen=True)
class TextSegment:
    """One run of text, optionally highlighted as unknown."""

    text: str
    highlight: bool = False


def language_label(lang_id: str) -> str:
    """A language id as people read it in the UI."""
    if not lang_id:
        return ""
    key = lang_id.lower()
    if key in _LABELS:
        return _LABELS[key]
    return lang_id.replace("_", " ").title()


def partition_picker_languages(langs: list[str]) -> tuple[list[str], list[str]]:
    """Split ordered language ids into human/natural targets and programming code."""
    human = [lang for lang in langs if is_natural_language(lang)]
    code = [lang for lang in langs if not is_natural_language(lang)]
    return human, code


def build_language_picker_entries(langs: list[str]) -> list[PickerEntry]:
    """Human languages first (order preserved), then an optional Code section."""
    human, code = partition_picker_languages(langs)
    entries = [PickerEntry("language", lang) for lang in human]
    if code:
        entries.append(PickerEntry("header", CODE_PICKER_GROUP))
        entries.extend(PickerEntry("language", lang) for lang in code)
    return entries


def picker_language_ids(entries: list[PickerEntry]) -> list[str]:
    return [entry.value for entry in entries if entry.kind == "language"]


def picker_header_display(label: str = CODE_PICKER_GROUP) -> str:
    return f"— {label} —"


def is_picker_header(value: str) -> bool:
    text = (value or "").strip()
    return text.startswith("— ") and text.endswith(" —")


def picker_combobox_values(entries: list[PickerEntry]) -> list[str]:
    """Values for a readonly ttk.Combobox (headers plus language ids)."""
    out: list[str] = []
    for entry in entries:
        if entry.kind == "header":
            out.append(picker_header_display(entry.value))
        else:
            out.append(entry.value)
    return out


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


def _merge_spans(length: int, spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not spans:
        return []
    ordered = sorted(spans)
    merged: list[tuple[int, int]] = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return [(a, min(b, length)) for a, b in merged if a < length]


def _spans_to_segments(text: str, spans: list[tuple[int, int]]) -> list[TextSegment]:
    if not text:
        return []
    if not spans:
        return [TextSegment(text, False)]
    out: list[TextSegment] = []
    pos = 0
    for start, end in spans:
        if pos < start:
            out.append(TextSegment(text[pos:start], False))
        if start < end:
            out.append(TextSegment(text[start:end], True))
        pos = end
    if pos < len(text):
        out.append(TextSegment(text[pos:], False))
    return out


def _unknown_word_spans(text: str, unknown: tuple[str, ...]) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for word in sorted({w for w in unknown if w}, key=len, reverse=True):
        start = 0
        while True:
            at = text.find(word, start)
            if at < 0:
                break
            spans.append((at, at + len(word)))
            start = at + len(word)
    return spans


def segment_result_text(body: str, unknown: tuple[str, ...] = ()) -> list[TextSegment]:
    """Highlight bracketed unknowns and any listed tokens in the translation body."""
    spans = [(m.start(), m.end()) for m in _BRACKETS.finditer(body or "")]
    occupied = list(spans)
    for start, end in _unknown_word_spans(body or "", unknown):
        if not any(a <= start and end <= b for a, b in occupied):
            spans.append((start, end))
    return _spans_to_segments(body or "", _merge_spans(len(body or ""), spans))


def segment_source_text(source: str, unknown: tuple[str, ...]) -> list[TextSegment]:
    """Highlight unknown source tokens when the From language is natural."""
    if not unknown:
        return [TextSegment(source or "", False)]
    return _spans_to_segments(source or "", _merge_spans(len(source or ""), _unknown_word_spans(source or "", unknown)))


def result_footer_text(full_result: str, body: str) -> str:
    """Metadata lines after the translation body (confidence, second opinion, etc.)."""
    if not full_result or not body or full_result == body:
        return ""
    if full_result.startswith(body):
        return full_result[len(body):].lstrip("\n")
    return ""


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