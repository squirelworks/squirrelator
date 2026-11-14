"""Split pasted prose into sentences and paragraphs for per-sentence translation.

Deterministic: the same text always yields the same sentence and paragraph
boundaries. Empty lines separate paragraphs; single newlines inside a block
are folded to spaces before sentence splitting.
"""

from __future__ import annotations

from .translate_ui import is_natural_language

_PROSE_SKIP = frozenset({"pseudocode"})
_SENTENCE_END = ".!?。！？"


def is_prose_language_pair(from_lang: str, to_lang: str) -> bool:
    """Both sides are human languages where sentence-by-sentence translation applies."""
    if not from_lang or not to_lang:
        return False
    if from_lang.lower() in _PROSE_SKIP or to_lang.lower() in _PROSE_SKIP:
        return False
    return is_natural_language(from_lang) and is_natural_language(to_lang)


def split_prose_paragraphs(text: str) -> list[str]:
    """Split source text into paragraph blocks. Blank lines (only whitespace) are
    separators; they are not included in the returned blocks."""
    if not text:
        return []
    paragraphs: list[str] = []
    current: list[str] = []
    for line in text.split("\n"):
        if line.strip() == "":
            if current:
                paragraphs.append("\n".join(current))
                current = []
        else:
            current.append(line)
    if current:
        paragraphs.append("\n".join(current))
    return paragraphs


def split_sentences(paragraph: str) -> list[str]:
    """Split one paragraph into sentences, keeping end punctuation on each piece."""
    collapsed = " ".join(paragraph.replace("\n", " ").split()).strip()
    if not collapsed:
        return []
    sentences: list[str] = []
    start = 0
    for i, ch in enumerate(collapsed):
        if ch not in _SENTENCE_END:
            continue
        j = i + 1
        while j < len(collapsed) and collapsed[j].isspace():
            j += 1
        piece = collapsed[start:j].strip()
        if piece:
            sentences.append(piece)
        start = j
    if start < len(collapsed):
        tail = collapsed[start:].strip()
        if tail:
            sentences.append(tail)
    return sentences if sentences else [collapsed]


def prose_needs_splitting(text: str) -> bool:
    """True when the text has more than one sentence or more than one paragraph."""
    paragraphs = split_prose_paragraphs(text)
    if len(paragraphs) > 1:
        return True
    if len(paragraphs) == 1 and len(split_sentences(paragraphs[0])) > 1:
        return True
    return False


def should_translate_prose(text: str, from_lang: str, to_lang: str) -> bool:
    return is_prose_language_pair(from_lang, to_lang) and prose_needs_splitting(text)


def join_translated_paragraphs(paragraph_texts: list[list[str]]) -> str:
    """Join translated sentences into paragraphs and paragraphs with blank lines."""
    blocks = [" ".join(sentences).strip() for sentences in paragraph_texts if sentences]
    return "\n\n".join(block for block in blocks if block)