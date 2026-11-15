import json

import pytest

from squirrelator import data, translate
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
    # 今日は is konnichiwa, hello, when that kanji spelling is the whole
    # utterance. Inside a sentence, 今日 and は keep today and @topic.
    assert words(analyze("今日は", "japanese")) == ["今日は"]
    assert words(analyze("今日は。", "japanese")) == ["今日は"]
    assert words(analyze("今日は暑いです。", "japanese")) == ["今日", "は", "暑い", "です"]
    # A vocab word still beats a split into three or more pieces.
    assert words(analyze("ありがとうございます", "japanese")) == ["ありがとう", "ございます"]


def test_column_row_surface_keeps_the_rows_tokens():
    # 吃饭 is also a vocab word meaning eat, but the eat-food row writes
    # 我吃饭 as 我+吃+饭. A restaurant row still keeps 吃饭 as one word.
    assert words(analyze("我吃饭。", "chinese")) == ["我", "吃", "饭"]
    assert words(analyze("我在饭馆吃饭。", "chinese")) == ["我", "在", "饭馆", "吃饭"]


def test_gloss_only_vocab_yields_to_a_full_affix_split():
    # jIyajbe' is a phrase card with only a gloss; the column writes
    # jI- + yaj + -be', and every piece has a meaning.
    assert words(analyze("jIyajbe'", "klingon")) == ["jI", "yaj", "be'"]
    assert [t.affix for t in analyze("jIyajbe'", "klingon") if t.kind == "word"] == [
        "prefix", "", "suffix",
    ]


@pytest.mark.parametrize("text", ["I do not understand", "I did not see it", "you do not know"])
def test_do_support_keeps_every_word_of_the_source(text):
    """Auxiliary do before not stays in the tokens, so joining them gives the
    source back, but it is support: known, and not a word to match."""
    tokens = analyze(text, "english")
    assert "".join(t.text for t in tokens) == text
    assert all(text[t.start:t.end] == t.text for t in tokens)
    assert all(t.known for t in tokens)
    aux = [t for t in tokens if t.support]
    assert [fold(t.text) for t in aux] in (["do"], ["did"])


def test_do_support_still_matches_dont_rows():
    assert translate("I do not understand", "english", "klingon") == "jIyajbe'"


def test_joiners_inside_words_keep_the_word_whole():
    """A Tibetan tsheg and an Indic zero-width non-joiner sit inside a word."""
    for text, language in [("ཕྲུ་གུ", "tibetan"), ("ರೆಸ್ಟೋರೆಂಟ್\u200cನಲ್ಲಿ", "kannada")]:
        tokens = analyze(text, language)
        assert "".join(t.text for t in tokens) == text
        assert all(t.kind == "word" and t.known for t in tokens)
