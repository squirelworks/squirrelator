import pytest

from squirrelator import Translation, UnsupportedLanguage, data, translate, translate_full
from squirrelator.pipeline import languages, run

try:
    data.data_dir()
except data.DataNotFound:
    pytest.skip("squirrel-lang-data not checked out", allow_module_level=True)


def test_translate_with_the_pipeline_engine():
    assert translate("バスで学校に行きます。", "japanese", "english", engine="pipeline") == "I go to school by bus."


def test_default_engine_is_unchanged():
    assert translate("print hello", "english", "python") == 'print("hello")'
    assert translate("print hello", "english", "python", engine="rules") == 'print("hello")'


def test_unknown_engine_is_an_error():
    with pytest.raises(ValueError):
        translate("hi", "english", "python", engine="neural")


def test_translate_full_gives_alternatives_breakdown_and_confidence(root):
    r = run("バスで学校に行きます。", "japanese", "english", root=root)
    assert isinstance(r, Translation)
    assert r.text == "I go to school by bus."
    assert "I take the bus to school." in r.alternatives
    [step] = r.breakdown
    assert step.source == "バスで学校に行きます。" and step.result == r.text
    assert "meaning matrix" in step.why
    assert r.confidence == 1.0 and r.alpha and r.unknown == ()
    assert translate_full("バスで学校に行きます。", "japanese", "english", engine="pipeline") == r


def test_each_clause_is_translated_and_joined_for_the_target(root):
    r = run("私は学生です。バスで学校に行きます！", "japanese", "hangul", root=root)
    assert r.text == "저는 학생이에요. 버스로 학교에 가요."
    assert len(r.breakdown) == 2


def test_unknown_words_are_listed_and_lower_confidence(root):
    r = run("I like xyzzy.", "english", "japanese", root=root)
    assert "[xyzzy]" in r.text
    assert "xyzzy" in r.unknown
    assert r.confidence < 0.5


def test_unsupported_language():
    with pytest.raises(UnsupportedLanguage):
        translate_full("hi", "english", "cobol", engine="pipeline")
    assert translate("hi", "english", "cobol", engine="pipeline").startswith("Unsupported")
    assert "english" in languages() and "japanese" in languages()


def test_kanji_konnichiwa_is_hello_and_a_sentence_stays_today(root):
    # 今日は is the kanji spelling of konnichiwa. On its own that is hello.
    # 今日は暑いです keeps today and the topic particle.
    assert run("今日は", "japanese", "english", root=root).text == "Hello."
    assert run("今日は。", "japanese", "english", root=root).text == "Hello."
    hot = run("今日は暑いです。", "japanese", "english", root=root).text
    assert hot != "Hello." and "today" in hot.casefold()


def test_same_language_and_empty_source(root):
    assert run(" 学生 ", "japanese", "japanese", root=root).text == "学生"
    assert run("", "japanese", "english", root=root).text == ""
