import json
from pathlib import Path

import pytest

from squirrelator import Step, Translation, UnsupportedLanguage, translate, translate_full
from squirrelator.translator import SUPPORTED

GOLDEN = json.loads((Path(__file__).parent / "golden" / "translations.json").read_text(encoding="utf-8"))
SUPPORTED_CASES = [
    c for c in GOLDEN
    if c["from"].strip().lower() in SUPPORTED and c["to"].strip().lower() in SUPPORTED
]


@pytest.mark.parametrize("case", SUPPORTED_CASES, ids=lambda c: f"{c['from'].strip()}->{c['to'].strip()}")
def test_text_is_what_translate_returns(case):
    r = translate_full(case["source"], case["from"], case["to"])
    assert r.text == translate(case["source"], case["from"], case["to"]) == case["expected"]
    assert str(r) == r.text
    assert 0.0 <= r.confidence <= 1.0
    assert all(isinstance(s, Step) for s in r.breakdown)


def test_unknown_language_raises():
    with pytest.raises(UnsupportedLanguage) as e:
        translate_full("print hello", "cobol", "python")
    assert e.value.lang == "cobol"
    assert "python" in e.value.supported
    # translate() keeps its old behavior for LSD.
    assert translate("print hello", "cobol", "python").startswith("Unsupported")


def test_matched_sentence():
    r = translate_full("print hello", "english", "python")
    assert r == Translation(
        'print("hello")',
        breakdown=(Step("print hello", 'print("hello")',
                        "Read as an instruction to print or show something."),),
        confidence=1.0,
        alpha=True,
    )


def test_unmatched_sentence_is_marked_unknown_not_guessed():
    r = translate_full("sort the list", "english", "python")
    assert r.unknown == ("sort the list",)
    assert r.confidence == 0.0
    assert r.breakdown == ()


def test_code_to_english_breakdown_and_unknown_lines():
    r = translate_full("for i in range(1, 4):\n    print(i)\nfoo()", "python", "english")
    assert [(s.source, s.result) for s in r.breakdown] == [
        ("for i in range(1, 4):", "Start a loop"),
        ("print(i)", "Print i"),
    ]
    assert r.unknown == ("foo()",)
    assert r.confidence == pytest.approx(2 / 3)


def test_lines_only_echoed_back_count_as_unknown():
    r = translate_full("SELECT 1;", "sql", "english")
    assert r.text == "Execute: SELECT 1;"
    assert r.unknown == ("SELECT 1;",)
    assert r.confidence == 0.0


def test_code_to_code_goes_through_english():
    r = translate_full('PRINT "Hi"', "quickbasic", "javascript")
    assert [s.result for s in r.breakdown] == ['Print "Hi"', r.text]
    assert r.confidence == 1.0


def test_every_pair_is_alpha_except_same_language():
    assert translate_full("x = 5", "python", "python").alpha is False
    assert translate_full("print hello", "english", "python").alpha is True


def test_breakdown_has_no_implementation_notes():
    for c in SUPPORTED_CASES:
        for s in translate_full(c["source"], c["from"], c["to"]).breakdown:
            assert "_" not in s.why and ".py" not in s.why
