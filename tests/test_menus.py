import pytest

from squirrelator import Step, Translation, data
from squirrelator.menus import ENGINE_IDS, ENGINES, PIPELINE, RULES, format_result, languages_for
from squirrelator.translator import SUPPORTED


def test_both_engines_are_offered_and_alpha_is_labelled():
    assert ENGINES == (RULES, PIPELINE)
    assert "alpha" in PIPELINE.lower()
    assert ENGINE_IDS == {RULES: "rules", PIPELINE: "pipeline"}


def test_rules_menu_lists_every_supported_language_once():
    langs = languages_for(RULES)
    assert sorted(langs) == sorted(SUPPORTED)
    assert langs[:3] == ["english", "klingon", "latin"]


def test_pipeline_menu_lists_the_data_languages():
    try:
        data.data_dir()
    except data.DataNotFound:
        pytest.skip("squirrel-lang-data not checked out")
    langs = languages_for(PIPELINE)
    assert "english" in langs and "japanese" in langs
    assert langs == sorted(langs)


def test_result_text_shows_alternatives_unknown_words_and_alpha():
    t = Translation("私好き[xyzzy]。", ("私は好き。",), (Step("I like xyzzy.", "私好き[xyzzy]。", "Word by word."),),
                    ("xyzzy",), 0.33, True)
    out = format_result(t)
    assert out.startswith("私好き[xyzzy]。")
    assert "Also:\n  私は好き。" in out
    assert "Not in the data yet: xyzzy" in out
    assert "Word by word." in out
    assert out.endswith("Alpha. Confidence 33%.")


def test_plain_result_is_just_the_text():
    assert format_result(Translation("hi", alpha=False)) == "hi"
