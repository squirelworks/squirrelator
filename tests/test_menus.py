import pytest

from squirrelator import Step, Translation, data
from squirrelator.menus import AUTO, ENGINE_IDS, ENGINES, PIPELINE, RULES, format_result, format_rules_result, languages_for, runs_pipeline
from squirrelator.translator import SUPPORTED


def test_auto_comes_first_and_alpha_is_labelled():
    # The menu matches translate(): Auto is the default and comes first.
    assert ENGINES == (AUTO, RULES, PIPELINE)
    assert "alpha" in PIPELINE.lower()
    assert ENGINE_IDS == {AUTO: "auto", RULES: "rules", PIPELINE: "pipeline"}


def test_auto_menu_lists_both_engines_languages():
    langs = languages_for(AUTO)
    assert len(langs) == len(set(langs))
    assert set(languages_for(RULES)) <= set(langs)
    assert set(languages_for(PIPELINE)) <= set(langs)
    code = [lang for lang in languages_for(RULES) if lang not in ("english", "klingon", "latin")]
    assert langs[-len(code):] == code          # pseudocode and code last, rules order
    human = langs[:-len(code)]
    assert human == sorted(human)               # human languages A to Z


def test_auto_shows_the_pipeline_result_only_for_pipeline_pairs():
    assert not runs_pipeline(AUTO, "english", "python")
    assert not runs_pipeline(AUTO, "english", "latin")   # Latin stays on rules
    assert not runs_pipeline(RULES, "japanese", "english")
    assert runs_pipeline(PIPELINE, "english", "python")
    try:
        data.data_dir()
    except data.DataNotFound:
        return
    assert runs_pipeline(AUTO, "japanese", "english")


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


def test_result_text_shows_the_second_opinion():
    other = Translation("Aquam bibō.", (), (), (), 1.0, True)
    out = format_result(Translation("# Could not match", alpha=False, second_opinion=other))
    assert out.startswith("# Could not match")
    assert out.endswith("Second opinion from Pipeline (alpha), confidence 100%:\n  Aquam bibō.")


def test_rules_result_text_is_unchanged_without_a_second_opinion():
    assert format_rules_result(Translation('print("hello")')) == 'print("hello")'
    other = Translation("Aquam bibō.", (), (), ("x",), 0.5, True)
    out = format_rules_result(Translation("# Could not match", second_opinion=other))
    assert out == ("# Could not match\n\nSecond opinion from Pipeline (alpha), confidence 50%:\n"
                   "  Aquam bibō.\n  Not in the data yet: x")
