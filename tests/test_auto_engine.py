"""engine="auto", the default: the pipeline for sentences between English,
Latin and Klingon, rules for every other pair rules supports, so those
results don't change, and the pipeline for pairs rules rejects."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from squirrelator import UnsupportedLanguage, data, translate, translate_full
from squirrelator.translator import SUPPORTED, _norm, _pipeline_first

GOLDEN = json.loads((Path(__file__).parent / "golden" / "translations.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", GOLDEN, ids=lambda c: f"{c['from'].strip()}->{c['to'].strip()}")
def test_default_gives_what_rules_gave(case):
    """Every recorded rules result, unsupported pairs included, is unchanged,
    except where auto gives an English, Latin or Klingon sentence the
    pipeline understood better."""
    args = case["source"], case["from"], case["to"]
    assert translate(*args) == case["expected"]
    if _pipeline_first(_norm(case["from"]), _norm(case["to"])):
        full = translate_full(*args)
        assert translate(*args, engine=full.engine) == case["expected"]
    else:
        assert translate(*args, engine="rules") == case["expected"]


def test_code_instructions_keep_the_rules_result_full():
    """A code instruction rules understands keeps the rules result between
    any of its languages; only second_opinion is added."""
    for frm in ("english", "latin", "klingon"):
        for to in ("english", "latin", "klingon", "python"):
            auto = translate_full("print hello", frm, to)
            assert replace(auto, second_opinion=None) == translate_full("print hello", frm, to, engine="rules")


def test_latin_and_klingon_sentences_go_to_the_pipeline():
    try:
        data.data_dir()
    except data.DataNotFound:
        pytest.skip("squirrel-lang-data not checked out")
    from squirrelator.inflections import inflections
    if not inflections("klingon"):
        pytest.skip("Klingon affix tables arrive in squirrel-lang-data v0.1.4")
    r = translate_full("I drink water.", "english", "latin")
    assert r == translate_full("I drink water.", "english", "latin", engine="pipeline")
    assert r.text == "Aquam bibō." and r.engine == "pipeline" and r.alpha
    assert translate("I drink water.", "english", "latin") == r.text
    # Rules understood none of it, so it gives no second opinion.
    assert r.second_opinion is None
    k = translate_full("The officers see the ships.", "english", "klingon")
    assert k.engine == "pipeline" and k.text == "Dujmey lulegh yaSpu'"
    assert translate("Duj vIlegh", "klingon", "english") == "I see the ship."
    # The other engines are unchanged.
    assert translate_full("I drink water.", "english", "latin", engine="rules").second_opinion is None
    assert translate_full("I drink water.", "english", "latin", engine="pipeline").second_opinion is None


def test_code_instructions_stay_on_rules_with_the_pipelines_second_opinion():
    try:
        data.data_dir()
    except data.DataNotFound:
        pytest.skip("squirrel-lang-data not checked out")
    r = translate_full("print hello", "english", "latin")
    assert r.engine == "rules" and r.text == translate("print hello", "english", "latin", engine="rules")
    assert r.second_opinion == translate_full("print hello", "english", "latin", engine="pipeline")
    # Code pairs never reach the pipeline.
    assert translate("print hello", "english", "python") == 'print("hello")'
    assert translate_full('dic "salve"', "latin", "python").second_opinion is None


def test_without_the_data_latin_stays_on_rules(monkeypatch, tmp_path):
    monkeypatch.setenv(data.ENV_VAR, str(tmp_path))
    assert translate("I drink water.", "english", "latin") == translate(
        "I drink water.", "english", "latin", engine="rules")


def test_no_second_opinion_outside_the_overlap_or_when_the_pipeline_understood_nothing():
    assert translate_full("print hello", "english", "python").second_opinion is None
    assert translate_full("print hello", "latin", "latin").second_opinion is None
    assert translate_full("xyzzy plugh", "klingon", "english").second_opinion is None


def test_pair_rules_rejects_goes_to_the_pipeline():
    try:
        data.data_dir()
    except data.DataNotFound:
        pytest.skip("squirrel-lang-data not checked out")
    assert "japanese" not in SUPPORTED
    assert translate("バスで学校に行きます。", "japanese", "english") == "I go to school by bus."
    full = translate_full("バスで学校に行きます。", "japanese", "english")
    assert full == translate_full("バスで学校に行きます。", "japanese", "english", engine="pipeline")
    assert full.alpha
    assert translate("I drink coffee.", "english", "hangul") == translate(
        "I drink coffee.", "english", "hangul", engine="pipeline")


def test_pair_neither_engine_knows_keeps_the_rules_answer():
    # python has no column and cobol is in neither engine.
    for frm, to in (("python", "japanese"), ("cobol", "python"), ("english", "cobol")):
        assert translate("hi", frm, to) == translate("hi", frm, to, engine="rules")
        assert translate("hi", frm, to).startswith("Unsupported")
    with pytest.raises(UnsupportedLanguage) as e:
        translate_full("hi", "python", "japanese")
    assert e.value.supported == sorted(SUPPORTED)


def test_without_the_data_auto_is_rules(monkeypatch, tmp_path):
    monkeypatch.setenv(data.ENV_VAR, str(tmp_path))
    assert translate("こんにちは", "japanese", "english") == translate(
        "こんにちは", "japanese", "english", engine="rules")
    assert translate("print hello", "english", "python") == 'print("hello")'


def test_unknown_engine_is_an_error():
    with pytest.raises(ValueError):
        translate("hi", "english", "python", engine="neural")
    with pytest.raises(ValueError):
        translate_full("hi", "english", "python", engine="neural")
