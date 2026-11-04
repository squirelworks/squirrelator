import pytest

from squirrelator import data
from squirrelator.lexicon import lexicon
from squirrelator.pipeline.analyze import analyze
from squirrelator.pipeline.generate import Candidate, generate
from squirrelator.pipeline.interlingua import Interlingua, Unit, interlingua
from squirrelator.pipeline.parse import parse
from squirrelator.pipeline.rank import rank

try:
    data.data_dir()
except data.DataNotFound:
    pytest.skip("squirrel-lang-data not checked out", allow_module_level=True)


def ranked(text, source, target, root):
    clauses = parse(analyze(text, source, lex=lexicon(source, root)), source, root=root)
    out = []
    for clause in clauses:
        il = interlingua(clause, source, root=root)
        out += rank(generate(il, target, root=root), il, source, root=root)
    return out


def test_matrix_sentence_outranks_the_gloss(root):
    found = ranked("I take the bus to school.", "english", "japanese", root)
    assert [r.candidate.method for r in found] == ["matrix", "words"]
    assert found[0].text == "バスで学校に行きます。"
    assert found[0].score > found[1].score


def test_first_english_wording_comes_first(root):
    found = ranked("バスで学校に行きます。", "japanese", "english", root)
    assert found[0].text == "I go to school by bus."
    assert [r.score for r in found] == sorted((r.score for r in found), reverse=True)


def test_grammar_the_row_lacks_lowers_the_score_and_says_why(root):
    # With English inflection tables the gloss ("I went to school.") is a
    # second candidate; the matrix row still comes first, marked down.
    r = ranked("学校に行きました。", "japanese", "english", root)[0]
    assert r.text == "I go to school."
    assert r.score < 1
    assert "@past" in r.note


def test_gloss_score_falls_with_missing_words():
    il = Interlingua((Unit("i", "I"), Unit("like", "like"), Unit("", "xyzzy")), (), (), ("xyzzy",))
    full = Candidate("私好き", "", "words")
    gap = Candidate("私好き[xyzzy]", "", "words", missing=("xyzzy",))
    a, b = rank([gap, full], il, "english")
    assert a.candidate is full and b.candidate is gap
    assert "1 word with no translation" in b.note


def test_ties_keep_generate_order():
    il = Interlingua((Unit("i", "I"),), (), (), ())
    first, second = Candidate("a", "", "words"), Candidate("b", "", "words")
    assert [r.candidate for r in rank([first, second], il, "english")] == [first, second]


def test_a_word_the_row_writes_has_the_rows_grammar():
    # The clause read います as "exist"; the row writes the same います as
    # @ongoing. It is the same word, so no grammar differs.
    from squirrelator.pipeline.rank import _grammar, _row_grammar
    tokens = (("モスクワ", "", "moscow"), ("に", "", "@place"), ("住んで", "", "live"), ("います", "", "@ongoing"))
    il = Interlingua((Unit("moscow", "モスクワ", ("@place",)), Unit("live", "住んで"), Unit("exist", "います")), (), (), ())
    forms = {"います": frozenset({"@polite", "@present"})}
    assert _grammar(il, tokens, forms) == _row_grammar(tokens, forms)


def test_ongoing_rows_outrank_the_gloss(root):
    from squirrelator.matrix import matrix
    if "live-moscow" not in matrix(root).columns.get("japanese", {}):
        pytest.skip("the Japanese live-moscow row arrives in squirrel-lang-data v0.1.3")
    found = ranked("モスクワに住んでいます。", "japanese", "english", root)
    assert found[0].text == "I live in Moscow."
    assert found[0].score == 1.0
