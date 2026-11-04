import pytest

from squirrelator import data
from squirrelator.lexicon import lexicon
from squirrelator.pipeline.analyze import analyze
from squirrelator.pipeline.interlingua import interlingua
from squirrelator.pipeline.parse import parse

try:
    data.data_dir()
except data.DataNotFound:
    pytest.skip("squirrel-lang-data not checked out", allow_module_level=True)


def meaning_of(text, language, root):
    clauses = parse(analyze(text, language, lex=lexicon(language, root)), language, root=root)
    return [interlingua(c, language, root=root) for c in clauses]


def test_japanese_dropped_subject_comes_back_as_implied(root):
    [il] = meaning_of("バスで学校に行きます。", "japanese", root)
    assert "bus-school" in il.matches
    implied = [u for u in il.units if u.implied]
    assert [u.meaning for u in implied] == ["i"]
    assert implied[0].text == ""                # nothing in the source said it
    assert il.meanings[0] == "i" and set(il.meanings) == {"i", "bus", "school", "go"}


def test_ambiguous_particle_takes_the_role_the_matrix_pairs_with_the_word(root):
    [il] = meaning_of("バスで学校に行きます", "japanese", root)
    roles = {u.meaning: u.roles for u in il.units if not u.implied}
    assert roles["bus"] == ("@means",)          # で could also be @place
    assert roles["school"] == ("@direction",)   # に could also be @place
    bus = next(u for u in il.units if u.meaning == "bus")
    assert "@place" in bus.role_alternatives[0]


def test_same_meanings_from_different_languages(root):
    [ja] = meaning_of("私は学生です。", "japanese", root)
    [ko] = meaning_of("저는 학생이에요.", "hangul", root)
    [zh] = meaning_of("我是学生。", "chinese", root)
    assert set(ja.meanings) == set(ko.meanings) == set(zh.meanings) == {"i", "student"}
    assert "i-am-student" in ja.matches and "i-am-student" in ko.matches and "i-am-student" in zh.matches


def test_english_matches_rows_without_inventing_anything(root):
    [il] = meaning_of("I take the bus to school.", "english", root)
    assert "bus-school" in il.matches
    assert not any(u.implied for u in il.units)


def test_unknown_words_stop_matching_and_are_reported(root):
    [il] = meaning_of("I like xyzzy.", "english", root)
    assert il.unknown == ("xyzzy",)
    assert il.matches == ()


def test_clause_features_pass_through(root):
    [il] = meaning_of("Salve, quid agis?", "latin", root)
    assert "@question" in il.features


def test_every_matrix_row_round_trips_through_its_columns(root):
    """For each tested language, rendering a matrix row and running it through
    Analyze, Parse and Interlingua finds that row again, unless a longer
    dictionary word swallowed a listed token."""
    import json

    from conftest import LANGUAGES

    misses = []
    for lang in LANGUAGES:
        path = root / "meaning" / "columns" / f"{lang}.jsonl"
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        sep = json.loads(lines[0]).get("sep", " ")
        for line in lines[1:]:
            row = json.loads(line)
            text = ""
            for word, _, _ in row["t"]:
                glue = not text or word.startswith("-") or text.endswith("-")
                text = text.rstrip("-") + ("" if glue else sep) + (word.strip("-") if len(word) > 1 else word)
            found = [m for il in meaning_of(text, lang, root) for m in il.matches]
            if row["sentence"] not in found:
                misses.append((lang, row["sentence"], text))
    # 我吃饭: the word list has 吃饭 (eat a meal) as one word, which the
    # row writes as 吃 + 饭.
    allowed = {("chinese", "eat-food")}
    assert {(lang, s) for lang, s, _ in misses} <= allowed, misses


def test_english_be_is_part_of_the_rows_wording(root):
    # "is" alone reads as exist, but "Where is the station?" is how English
    # says the where-station row, so the row still matches.
    [il] = meaning_of("Where is the station?", "english", root)
    assert il.matches[0] == "where-station"
    [il] = meaning_of("I am a student.", "english", root)
    assert il.matches[0] == "i-am-student"
    assert il.unknown == ()


def test_a_word_outside_the_rows_wording_still_blocks_it(root):
    [il] = meaning_of("I am xyzzy.", "english", root)
    assert il.matches == ()
    assert set(il.unknown) == {"am", "xyzzy"}


def test_the_row_with_more_of_the_words_comes_first(root):
    [il] = meaning_of("How much is it?", "english", root)
    assert il.matches[0] == "how-much-is-it"


def test_english_rows_round_trip(root):
    """Every English wording of every row finds that row first, except the
    ones that need more than the data has yet (contractions, "do" questions,
    third-person verbs)."""
    from squirrelator.matrix import matrix

    misses = []
    for row in matrix(root).rows.values():
        for en in (row.en, *row.also):
            found = [m for il in meaning_of(en, "english", root) for m in il.matches]
            if not found or found[0] != row.id:
                misses.append(row.id)
    allowed = {
        "dont-understand", "dont-know", "love-you", "we-are-klingons", "cold-today", "raining",
        "have-cat", "house-big", "delicious", "head-hurts", "bus-school", "where-going",
        "going-home", "we-going-home", "lets-go", "child-sleeps", "officer-sees-child",
        "captain-sees-ship",
    }
    assert set(misses) <= allowed, sorted(set(misses) - allowed)


def test_a_word_the_column_writes_reads_as_the_row_reads_it(root):
    # 有 is have first in the word list; the column writes it as exist in
    # there-is-cat, so the row still matches.
    from squirrelator.matrix import matrix
    if "there-is-cat" not in matrix(root).columns.get("chinese", {}):
        pytest.skip("the Chinese there-is-cat row arrives in squirrel-lang-data v0.1.3")
    [il] = meaning_of("有一只猫。", "chinese", root)
    assert il.matches[0] == "there-is-cat"
