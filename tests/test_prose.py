from squirrelator.prose import (
    join_translated_paragraphs,
    prose_needs_splitting,
    should_translate_prose,
    split_prose_paragraphs,
    split_sentences,
)


def test_split_prose_paragraphs_empty_lines():
    assert split_prose_paragraphs("First.\n\nSecond.") == ["First.", "Second."]
    assert split_prose_paragraphs("One line.\nStill one.\n\nNew block.") == [
        "One line.\nStill one.",
        "New block.",
    ]


def test_split_sentences_latin_and_cjk():
    assert split_sentences("Hello. World.") == ["Hello.", "World."]
    assert split_sentences("今日は晴れ。明日は雨。") == ["今日は晴れ。", "明日は雨。"]


def test_prose_detection():
    assert not prose_needs_splitting("Only one.")
    assert prose_needs_splitting("One.\n\nTwo.")
    assert prose_needs_splitting("One. Two.")
    assert not prose_needs_splitting("Hello.")
    assert should_translate_prose("A. B.", "english", "latin")
    assert not should_translate_prose("print hello\nprint world", "english", "python")
    assert not should_translate_prose("One. Two.", "english", "pseudocode")


def test_join_translated_paragraphs():
    assert join_translated_paragraphs([["Hi."], ["Bye.", "Later."]]) == "Hi.\n\nBye. Later."