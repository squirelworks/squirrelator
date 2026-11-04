import pytest

from squirrelator import data
from squirrelator.lexicon import lexicon
from squirrelator.matrix import matrix
from squirrelator.pipeline.analyze import analyze
from squirrelator.pipeline.generate import generate, render
from squirrelator.pipeline.interlingua import interlingua
from squirrelator.pipeline.parse import parse

try:
    data.data_dir()
except data.DataNotFound:
    pytest.skip("squirrel-lang-data not checked out", allow_module_level=True)


def candidates(text, source, target, root):
    clauses = parse(analyze(text, source, lex=lexicon(source, root)), source, root=root)
    return [c for clause in clauses for c in generate(interlingua(clause, source, root=root), target, root=root)]


def words(text, source, target, root):
    [c] = [c for c in candidates(text, source, target, root) if c.method == "words"]
    return c


def test_render_glues_hyphenated_tokens():
    assert render(["저", "-는", "학생", "-이에요"], " ", ".") == "저는 학생이에요."
    assert render(["ال-", "بيت"], " ") == "البيت"
    assert render(["私", "は", "学生"], "") == "私は学生"


def test_matrix_row_comes_first_with_every_english_wording(root):
    found = candidates("バスで学校に行きます。", "japanese", "english", root)
    assert found[0].text == "I go to school by bus."
    assert found[0].method == "matrix" and found[0].row == "bus-school"
    assert "I take the bus to school." in [c.text for c in found]


def test_matrix_row_in_another_column(root):
    found = candidates("バスで学校に行きます。", "japanese", "hangul", root)
    assert found[0].text == "버스로 학교에 가요."
    assert found[0].reading == "beoseu ro hakgyo e gayo"


def test_words_follow_the_target_word_order(root):
    # Japanese and Korean put the verb last; the matrix rows say so.
    assert words("I take the bus to school.", "english", "japanese", root).text.endswith("行きます。")
    assert words("I drink coffee.", "english", "hangul", root).text == "저 커피 마셔요."


def test_unknown_words_stay_in_brackets_and_are_listed(root):
    c = words("I like xyzzy.", "english", "japanese", root)
    assert "[xyzzy]" in c.text
    assert c.missing == ("xyzzy",)


def test_markers_the_target_lacks_are_dropped_not_invented(root):
    c = words("저는 물을 좋아해요.", "hangul", "english", root)
    assert c.text == "I like water."
    assert "as for" not in c.text.casefold()
    assert "@topic" in c.dropped


def test_markers_go_where_the_target_puts_them(root):
    # Korean -로 follows its word; English "by" goes before it.
    c = words("I go to school by bus.", "english", "hangul", root)
    assert "버스로" in c.text


def test_every_row_reaches_english_through_the_pipeline(root):
    """Each row of the tested columns, run through the whole pipeline into
    English, gives the row's own English sentence as a candidate."""
    mx = matrix(root)
    misses = []
    for lang in ("chinese", "hangul", "japanese", "latin"):
        for row_id, rendering in mx.columns.get(lang, {}).items():
            text = render([t for t, _, _ in rendering.tokens], rendering.sep, rendering.end)
            if mx.rows[row_id].en not in [c.text for c in candidates(text, lang, "english", root)]:
                misses.append((lang, row_id))
    # The same rows Interlingua can't find again (tests/test_interlingua.py).
    allowed = {("japanese", "thank-you-very-much"), ("japanese", "hot-today"), ("chinese", "going-home")}
    assert set(misses) <= allowed, misses
