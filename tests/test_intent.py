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


def test_parse_input():
    assert parse_intent("ask for name") == Intent("input", name="name")
    assert parse_intent("ask the user for age") == Intent("input", name="age")
    assert parse_intent("input score") == Intent("input", name="score")
    assert parse_intent("read line from the user") == Intent("input", name="line")


def test_parse_if_then_print():
    got = parse_intent("if x > 5 print ready")
    assert got == Intent(
        "if", name="x", start=">", end="5", body=Intent("output", name="ready")
    )
    got = parse_intent("if count is greater than 10 then print full")
    assert got.kind == "if" and got.start == ">" and got.body.name == "full"


def test_parse_if_else_print():
    got = parse_intent("if x > 5 print ready else print wait")
    assert got == Intent(
        "if",
        name="x",
        start=">",
        end="5",
        body=Intent("output", name="ready"),
        alt=Intent("output", name="wait"),
    )
    got = parse_intent("if n is less than 3 then print small else print big")
    assert got.alt is not None and got.alt.name == "big" and got.start == "<"


def test_generate_python_matches_rules_shapes():
    assert generate(Intent("output", name="hello"), "python") == 'print("hello")'
    assert generate(Intent("loop", start="1", end="5"), "python") == (
        "for i in range(1, 6):\n    print(i)"
    )
    assert generate(Intent("assignment", name="total", start="42"), "python") == "total = 42"
    assert generate(Intent("input", name="name"), "python") == "name = input()"
    assert generate(Intent("input", name="name"), "javascript") == "let name = prompt();"
    assert generate(Intent("input", name="name"), "shell") == "read name"
    assert generate(Intent("input", name="name"), "cobol") is None
    assert generate(Intent("output", name="hi"), "cobol") is None
    iff = Intent("if", name="x", start=">", end="5", body=Intent("output", name="ready"))
    assert generate(iff, "python") == 'if x > 5:\n    print("ready")'
    assert generate(iff, "javascript") == 'if (x > 5) {\n  console.log("ready");\n}'
    ifelse = Intent(
        "if",
        name="x",
        start=">",
        end="5",
        body=Intent("output", name="ready"),
        alt=Intent("output", name="wait"),
    )
    assert generate(ifelse, "python") == (
        'if x > 5:\n    print("ready")\nelse:\n    print("wait")'
    )
    assert generate(ifelse, "javascript") == (
        'if (x > 5) {\n  console.log("ready");\n}'
        ' else {\n  console.log("wait");\n}'
    )
    assert generate(ifelse, "shell") == (
        'if [ "$x" -gt 5 ]; then\n  echo "ready"\nelse\n  echo "wait"\nfi'
    )


def test_match_natural_uses_intent_without_changing_outputs():
    assert _match_natural("print hello", "python") == ("output", 'print("hello")')
    assert _match_natural("count from 1 to 5", "python")[0] == "loop"
    assert _match_natural("set x to 1", "python") == ("assignment", "x = 1")
    assert _match_natural("ask for name", "python") == ("input", "name = input()")
    assert _match_natural("sort the list", "python")[0] is None
    assert _match_natural("if x > 5 print ready", "python") == (
        "if",
        'if x > 5:\n    print("ready")',
    )
    assert _match_natural("if x > 5 print ready else print wait", "python") == (
        "if",
        'if x > 5:\n    print("ready")\nelse:\n    print("wait")',
    )
