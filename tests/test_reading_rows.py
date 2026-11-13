"""Rows matched through a word's other meanings, contractions, glued
prefixes, and phrases that carry no meaning."""

import json

import pytest

from squirrelator.pipeline.analyze import analyze
from squirrelator.pipeline.parse import grammar_only
from squirrelator.translator import translate_full


def words(text, language):
    return [(t.text, t.affix) for t in analyze(text, language) if t.kind == "word"]


@pytest.mark.parametrize("source, target, expected", [
    # "love" is like first and love second; love-you has love.
    ("I love you.", "japanese", "あなたを愛しています。"),
    # "house" is home first; house-big has house.
    ("The house is big.", "hangul", "집이 커요."),
    # "have" is eat first (have lunch); have-cat has have.
    ("I have a cat.", "greek", "Έχω μια γάτα."),
])
def test_a_word_reads_as_the_meaning_the_row_has(source, target, expected):
    assert translate_full(source, "english", target).text == expected


@pytest.mark.parametrize("source, target, expected", [
    ("It's cold today.", "greek", "Σήμερα κάνει κρύο."),
    ("It's delicious.", "japanese", "おいしいです。"),
])
def test_a_contraction_in_the_rows_wording_is_its_pieces(source, target, expected):
    assert translate_full(source, "english", target).text == expected


def test_a_meaningless_phrase_does_not_swallow_words_that_have_meanings():
    # The Greek vocab has the card "το τσάι" with only a gloss; the column
    # gives το (@the) and τσάι (tea).
    assert words("Πίνω το τσάι.", "greek") == [("Πίνω", ""), ("το", ""), ("τσάι", "")]
    assert translate_full("Πίνω το τσάι.", "greek", "english").text == "I drink tea."


def test_grammar_only_needs_every_part_to_be_grammar():
    assert grammar_only("@the")
    assert grammar_only("@place+@the")
    assert not grammar_only("@copula+he")
    assert not grammar_only("meet+@past")
    assert not grammar_only("")


def _has_column(root, language):
    return (root / "meaning" / "columns" / f"{language}.jsonl").is_file()


@pytest.fixture
def french(root):
    if not _has_column(root, "french"):
        pytest.skip("the pinned data has no French column yet")
    return root


def test_french_elision_with_a_content_meaning_heads_its_own_phrase(french):
    assert translate_full("J'aime le café.", "french", "english").text == "I like coffee."
    assert translate_full("Je suis d'Égypte.", "french", "english").text == "I am from Egypt."


def test_a_glued_prefix_before_a_phrase(french):
    # J'ai mal: j' then the phrase "ai mal", not j' + ai + an unknown mal.
    assert words("J'ai mal à la tête.", "french")[:2] == [("J'", "prefix"), ("ai mal", "")]
    assert translate_full("J'ai faim.", "french", "english").text == "I am hungry."


def test_a_vocab_card_with_only_a_gloss_splits_into_meanings(french):
    assert words("l'eau", "french") == [("l'", "prefix"), ("eau", "")]


def test_every_french_column_row_reads_back_as_its_english(french):
    rows = {}
    for line in (french / "meaning" / "sentences.jsonl").read_text(encoding="utf-8").splitlines()[1:]:
        row = json.loads(line)
        rows[row["id"]] = row
    from squirrelator.pipeline.generate import render
    lines = (french / "meaning" / "columns" / "french.jsonl").read_text(encoding="utf-8").splitlines()
    misses = []
    for line in lines[1:]:
        r = json.loads(line)
        source = render([t[0] for t in r["t"]], " ", r.get("end", ""))
        got = translate_full(source, "french", "english").text
        if got not in (rows[r["sentence"]]["en"], *rows[r["sentence"]].get("also", ())):
            misses.append((source, got))
    # est-il is both "is it" and "is he", and C'est both "it is" and "this
    # is", so a few rows read as their neighbour.
    assert len(misses) <= 3, misses
