import pytest

from squirrelator import data
from squirrelator.inflections import inflections
from squirrelator.lexicon import lexicon
from squirrelator.pipeline.analyze import analyze
from squirrelator.pipeline.generate import generate
from squirrelator.pipeline.interlingua import Interlingua, Unit, interlingua
from squirrelator.pipeline.parse import parse
from squirrelator.pipeline.rank import rank

try:
    data.data_dir()
except data.DataNotFound:
    pytest.skip("squirrel-lang-data not checked out", allow_module_level=True)


def ranked(text, source, target, root):
    [clause] = parse(analyze(text, source, lex=lexicon(source, root)), source, root=root)
    il = interlingua(clause, source, root=root)
    return il, rank(generate(il, target, root=root), il, source, root=root)


def test_tables_load_with_forms_and_features(root):
    [go] = [w for w in inflections("japanese", root) if w.lemma == "行く"]
    assert go.meaning == "go"
    assert go.form("polite-past").text == "行きました"
    assert go.form("polite-past").features == {"@polite", "@past"}


def test_no_table_means_no_words(root):
    assert inflections("klingon", root) == ()


def test_analyze_knows_inflected_forms(root):
    [token] = [t for t in analyze("行きました", "japanese", lex=lexicon("japanese", root)) if t.kind == "word"]
    assert token.known
    assert {e.meaning for e in token.entries} == {"go+@past+@polite"}


def test_past_tense_reaches_the_clause_and_the_rank_note(root):
    il, [best, *_] = ranked("学校に行きました。", "japanese", "english", root)
    [go] = [u for u in il.units if u.meaning == "go"]
    assert "@past" in go.roles
    assert best.text == "I go to school."
    assert best.score < 1 and "@past" in best.note


def test_same_form_as_the_row_is_no_mismatch(root):
    _, [best, *_] = ranked("学校に行きます。", "japanese", "english", root)
    assert (best.text, best.score) == ("I go to school.", 1.0)


def test_stem_and_ending_rows_match_a_whole_inflected_form(root):
    # The row writes 分かり + ません; the table knows 分かりません whole.
    _, [best, *_] = ranked("分かりません。", "japanese", "english", root)
    assert (best.text, best.score) == ("I don't understand.", 1.0)


def test_generate_picks_the_form_in_the_columns_register(root):
    # The column writes 行きます, so past is 行きました, not plain 行った.
    il = Interlingua((Unit("go", "went", ("@past",)),), (), (), ())
    [c] = generate(il, "japanese", root=root)
    assert c.text.startswith("行きました")
    assert c.dropped == ()
