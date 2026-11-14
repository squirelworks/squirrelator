from squirrelator import Step
from squirrelator.translate_ui import (
    format_alternatives_lines,
    format_breakdown_rows,
    language_label,
    swap_translate_state,
)


def test_language_label():
    assert language_label("english") == "English"
    assert language_label("quickbasic") == "QuickBASIC"
    assert language_label("lolcode") == "LOLCODE"
    assert language_label("z80") == "Z80 Assembly"
    assert language_label("") == ""


def test_swap_swaps_languages_only_when_result_empty():
    assert swap_translate_state("english", "python", "print hello", "") == (
        "python",
        "english",
        "print hello",
        "",
    )


def test_swap_moves_result_into_source_when_present():
    assert swap_translate_state("english", "french", "hello", "bonjour") == (
        "french",
        "english",
        "bonjour",
        "hello",
    )


def test_format_alternatives_lines_skips_blanks():
    assert format_alternatives_lines(("A", "", "B")) == ["A", "B"]
    assert format_alternatives_lines(()) == []


def test_format_breakdown_rows_maps_steps():
    rows = format_breakdown_rows(
        (Step("print hello", 'print("hello")', "Read as an instruction."), Step("", "", ""))
    )
    assert len(rows) == 1
    assert rows[0].dictionary_form == "print hello"
    assert rows[0].meaning_unit == 'print("hello")'
    assert rows[0].note == "Read as an instruction."
    assert rows[0].summary == "print hello"


def test_format_breakdown_rows_empty():
    assert format_breakdown_rows(()) == []


def test_swap_clears_empty_result_after_moving_text():
    assert swap_translate_state("english", "python", "", 'print("x")') == (
        "python",
        "english",
        'print("x")',
        "",
    )