"""Phase 4 intent grammar: parse English instructions into Intents."""

from squirrelator.intent import Intent, generate, parse_intent
from squirrelator.translator import _match_natural


def test_parse_output_print_and_bare_hello():
    assert parse_intent("print hello") == Intent("output", name="hello")
    assert parse_intent("show 'Good morning'") == Intent("output", name="good morning")
    assert parse_intent("say hello to everyone") == Intent("output", name="Hello")


def test_parse_loop_and_assignment():
    assert parse_intent("count from 1 to 5") == Intent("loop", start="1", end="5")
    assert parse_intent("loop 3 through 7") == Intent("loop", start="3", end="7")
    assert parse_intent("set total to 42") == Intent("assignment", name="total", start="42")
    assert parse_intent("make name = 'Ada'") == Intent(
        "assignment", name="name", start="'ada'"
    )


def test_parse_unknown_is_none():
    assert parse_intent("sort the list") is None
    assert parse_intent("") is None


def test_generate_python_matches_rules_shapes():
    assert generate(Intent("output", name="hello"), "python") == 'print("hello")'
    assert generate(Intent("loop", start="1", end="5"), "python") == (
        "for i in range(1, 6):\n    print(i)"
    )
    assert generate(Intent("assignment", name="total", start="42"), "python") == "total = 42"
    assert generate(Intent("output", name="hi"), "cobol") is None


def test_match_natural_uses_intent_without_changing_outputs():
    assert _match_natural("print hello", "python") == ("output", 'print("hello")')
    assert _match_natural("count from 1 to 5", "python")[0] == "loop"
    assert _match_natural("set x to 1", "python") == ("assignment", "x = 1")
    assert _match_natural("sort the list", "python")[0] is None
