"""The structured result of a translation.

translate() keeps returning a plain string for older callers such as
LanguageStudentDesk. translate_full() returns a Translation with everything
the UI's Alternatives and Breakdown views need.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Step:
    """One line of the breakdown: which part of the source became which part
    of the result, and why, in plain words."""

    source: str
    result: str
    why: str


@dataclass(frozen=True)
class Translation:
    """A translation with its alternatives and the reasons behind it.

    text          the main translation (what translate() returns)
    alternatives  other acceptable translations, best first
    breakdown     Steps explaining how the source became the text
    unknown       parts of the source no rule understood, shown, not guessed
    confidence    share of the source a rule understood, from 0.0 to 1.0
    alpha         True until this language pair's test set passes
    second_opinion  the other engine's Translation, for a pair both engines
                  know (english, latin and klingon under engine="auto"),
                  or None
    """

    text: str
    alternatives: tuple[str, ...] = ()
    breakdown: tuple[Step, ...] = ()
    unknown: tuple[str, ...] = ()
    confidence: float = 0.0
    alpha: bool = True
    from_lang: str = field(default="", compare=False)
    to_lang: str = field(default="", compare=False)
    second_opinion: Optional["Translation"] = None

    def __str__(self) -> str:
        return self.text


class UnsupportedLanguage(ValueError):
    """from_lang or to_lang isn't a language squirrelator knows."""

    def __init__(self, lang: str, supported: list[str]):
        self.lang = lang
        self.supported = supported
        super().__init__(f"Unsupported language: {lang}. Supported: {', '.join(supported)}")
