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

    from conftest import MARKERS

    misses = []
    for lang in MARKERS:
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
    allowed = {("japanese", "thank-you-very-much"), ("japanese", "hot-today"), ("chinese", "going-home")}
    assert {(lang, s) for lang, s, _ in misses} <= allowed, misses
