"""engine="auto", the default: rules for every pair rules supports, so
those results don't change, and the pipeline only for pairs rules rejects."""

import json
from pathlib import Path

import pytest

from squirrelator import UnsupportedLanguage, data, translate, translate_full
from squirrelator.translator import SUPPORTED

GOLDEN = json.loads((Path(__file__).parent / "golden" / "translations.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", GOLDEN, ids=lambda c: f"{c['from'].strip()}->{c['to'].strip()}")
def test_default_gives_what_rules_gave(case):
    """Every recorded rules result, unsupported pairs included, is unchanged."""
    args = case["source"], case["from"], case["to"]
    assert translate(*args) == translate(*args, engine="rules") == case["expected"]


def test_rules_pairs_stay_on_rules_full():
    for frm in ("english", "latin", "klingon"):
        for to in ("english", "latin", "klingon", "python"):
            assert translate_full("print hello", frm, to) == translate_full("print hello", frm, to, engine="rules")


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
