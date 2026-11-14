from squirrelator import Step
from squirrelator.menus import AUTO, languages_for
from squirrelator.translate_ui import (
    CODE_PICKER_GROUP,
    build_language_picker_entries,
    format_alternatives_lines,
    format_breakdown_rows,
    is_natural_language,
    is_picker_header,
    language_label,
    partition_picker_languages,
    picker_combobox_values,
    picker_language_ids,
    result_footer_text,
    segment_result_text,
    segment_source_text,
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


def test_is_natural_language():
    assert is_natural_language("english")
    assert is_natural_language("japanese")
    assert not is_natural_language("python")
    assert is_natural_language("pseudocode")


def test_picker_groups_code_after_human_languages():
    langs = languages_for(AUTO)
    human, code = partition_picker_languages(langs)
    assert human == [lang for lang in langs if is_natural_language(lang)]
    assert code == [lang for lang in langs if not is_natural_language(lang)]
    assert code
    entries = build_language_picker_entries(langs)
    assert picker_language_ids(entries) == langs
    headers = [e for e in entries if e.kind == "header"]
    assert len(headers) == 1
    assert headers[0].value == CODE_PICKER_GROUP
    idx = next(i for i, e in enumerate(entries) if e.kind == "header")
    assert [e.value for e in entries[idx + 1 :]] == code
    combo_values = picker_combobox_values(entries)
    assert is_picker_header(combo_values[idx])
    assert combo_values[idx + 1] == code[0]


def test_picker_skips_code_group_when_no_programming_targets():
    entries = build_language_picker_entries(["english", "japanese"])
    assert all(e.kind == "language" for e in entries)
    assert picker_combobox_values(entries) == ["english", "japanese"]


def test_segment_result_text_highlights_brackets():
    segs = segment_result_text("I like [xyzzy].", ("xyzzy",))
    assert any(s.highlight and "[xyzzy]" in s.text for s in segs)
    assert "".join(s.text for s in segs) == "I like [xyzzy]."


def test_segment_source_text_highlights_unknown_words():
    segs = segment_source_text("hello xyzzy world", ("xyzzy",))
    highlighted = "".join(s.text for s in segs if s.highlight)
    assert highlighted == "xyzzy"


def test_result_footer_text_after_body():
    full = "Hi.\n\nAlpha. Confidence 50%."
    assert result_footer_text(full, "Hi.") == "Alpha. Confidence 50%."