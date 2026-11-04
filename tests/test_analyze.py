import json

import pytest

from squirrelator import data
from squirrelator.lexicon import available, fold, lexicon
from squirrelator.pipeline.analyze import analyze

try:
    data.data_dir()
except data.DataNotFound:
    pytest.skip("squirrel-lang-data not checked out", allow_module_level=True)


def words(tokens):
    return [t.text for t in tokens if t.kind == "word"]


def meanings(tokens):
    return [next((e.meaning for e in t.entries if e.meaning), None) for t in tokens if t.kind == "word"]


def test_fold_drops_latin_accents_only():
    assert fold("Salvē") == "salve"
    assert fold("Ἀθῆναι") == fold("Αθηναι")
    assert fold("が") == "が"  # kana voicing is a different letter, not an accent
    assert fold("हिन्दी") == "हिन्दी"


@pytest.mark.parametrize("text, language, expected", [
    ("私は学生です。", "japanese", ["私", "は", "学生", "です"]),
    ("バスで学校に行きます", "japanese", ["バス", "で", "学校", "に", "行きます"]),
    ("我是学生。", "chinese", ["我", "是", "学生"]),
    ("ผมเป็นนักเรียน", "thai", ["ผม", "เป็น", "นักเรียน"]),
    ("Nomen mihi est Anna.", "latin", ["Nomen", "mihi", "est", "Anna"]),
    ("I take the bus to school.", "english", ["I", "take", "the", "bus", "to", "school"]),
])
def test_segments_and_finds_every_word(text, language, expected):
    tokens = analyze(text, language)
    assert words(tokens) == expected
    assert all(t.known for t in tokens)


def test_meaning_units_come_from_the_data():
    assert meanings(analyze("私は学生です", "japanese")) == ["i", "@topic", "student", "@copula"]
    assert meanings(analyze("I take the bus", "english")) == ["i", "go", "@the", "bus"]


def test_unknown_words_are_marked_not_guessed():
    tokens = analyze("I like xyzzy", "english")
    unknown = [t.text for t in tokens if not t.known]
    assert "xyzzy" in unknown
    tokens = analyze("学生ｑｑｑです", "japanese")
    assert [(t.text, t.known) for t in tokens] == [("学生", True), ("ｑｑｑ", False), ("です", True)]


def test_tokens_cover_the_whole_source():
    for text, language in [("Salve, amice!  42 times.", "latin"), ("私は、学生です。", "japanese")]:
        tokens = analyze(text, language)
        assert "".join(t.text for t in tokens) == text
        assert all(text[t.start:t.end] == t.text for t in tokens)


def test_numbers_and_punctuation_are_known():
    kinds = [(t.text, t.kind) for t in analyze("Count 3, now!", "english") if t.kind != "space"]
    assert kinds == [("Count", "word"), ("3", "number"), (",", "punct"), ("now", "word"), ("!", "punct")]


def surface(tokens, sep):
    """Write a column's tokens as text: affixes ("ال-", "-ك") glue to their
    neighbour without the hyphen; other tokens are joined by sep."""
    out = ""
    for i, t in enumerate(tokens):
        glue = i == 0 or t.startswith("-") or tokens[i - 1].endswith("-")
        out += ("" if glue else sep) + (t.strip("-") if len(t) > 1 else t)
    return out


def coarsens(got, expected):
    """True when got is expected with some neighbouring tokens joined, e.g.
    ありがとう + ございます found as the one dictionary word."""
    def key(s):
        return fold(s.replace(" ", "").strip("-"))
    i = 0
    for g in got:
        j, joined = i, ""
        while j < len(expected) and key(joined) != key(g):
            joined += expected[j].strip("-") if len(expected[j]) > 1 else expected[j]
            j += 1
        if key(joined) != key(g):
            return False
        i = j
    return i == len(expected)


def test_every_column_sentence_segments_back_into_its_tokens():
    """Each sentence of the meaning matrix, written out, segments into the
    tokens the data lists, or into longer words the word list also has.
    Every token must be known."""
    root = data.data_dir()
    failures = []
    for path in sorted((root / "meaning" / "columns").glob("*.jsonl")):
        lines = path.read_text(encoding="utf-8").splitlines()
        sep = json.loads(lines[0]).get("sep", " ")
        for line in lines[1:]:
            row = json.loads(line)
            expected = [t[0] for t in row["t"]]
            tokens = analyze(surface(expected, sep), path.stem)
            got = words(tokens)
            # Spaced languages may split a phrase into known words (לבית ספר);
            # unspaced ones must find the listed words or longer ones.
            if (not sep and not coarsens(got, expected)) or not all(t.known for t in tokens):
                failures.append((path.stem, row["sentence"], expected, got))
    assert failures == []


def test_affixes_split_off_only_when_every_part_is_known():
    tokens = [t for t in analyze("저는 학생이에요", "hangul") if t.kind == "word"]
    assert [(t.text, t.affix) for t in tokens] == [("저", ""), ("는", "suffix"), ("학생", ""), ("이에요", "suffix")]
    tokens = [t for t in analyze("zzz는", "hangul") if t.kind == "word"]
    assert [(t.text, t.known) for t in tokens] == [("zzz는", False)]


def test_phrases_and_letter_apostrophes():
    assert words(analyze("Γεια σου!", "greek")) == ["Γεια σου"]
    assert words(analyze("Qapla'!", "klingon")) == ["Qapla'"]


def test_available_languages_include_the_data_languages():
    langs = available()
    assert {"english", "japanese", "chinese", "latin", "klingon"} <= set(langs)
    assert langs == sorted(langs)


def test_lexicon_is_loaded_once():
    assert lexicon("japanese") is lexicon("japanese")


def test_words_with_a_meaning_win_over_a_bare_vocab_word():
    # 今日は is also the greeting (vocab only, no meaning); 今日 + は carry
    # today and @topic, so the sentence splits.
    assert words(analyze("今日は暑いです。", "japanese")) == ["今日", "は", "暑い", "です"]
    # A vocab word still beats a split into three or more pieces.
    assert words(analyze("ありがとうございます", "japanese")) == ["ありがとう", "ございます"]
