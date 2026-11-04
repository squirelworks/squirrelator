"""Golden tests: the exact output of translate() for every behavior that
works today, so the engine refactor (roadmap Phase 1) can't change it by
accident.

The cases and their expected outputs live in tests/golden/translations.json.
When a PR changes an output on purpose, regenerate the file and say so in
the PR body:

    python tests/test_golden.py --update
"""

import json
import sys
from pathlib import Path

import pytest

if __name__ == "__main__":  # run as a script from a fresh checkout
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from squirrelator import translate  # noqa: E402

GOLDEN = Path(__file__).parent / "golden" / "translations.json"

# Natural-language inputs, one per pattern the engine knows, plus one it doesn't.
NATURAL = [
    "print hello",
    "show 'Good morning'",
    "say hello to everyone",
    "count from 1 to 5",
    "loop 3 through 7",
    "set total to 42",
    "make name = 'Ada'",
    "sort the list",
]

# Code inputs, one or more per language the engine explains.
CODE = {
    "python": [
        'print("hi")',
        "for i in range(1, 4):\n    print(i)",
        "x = 5",
        "# just a comment",
    ],
    "javascript": ['console.log("hi");', "for (let i = 1; i <= 3; i++) {\n  console.log(i);\n}"],
    "quickbasic": ['PRINT "Hi"', "FOR i = 1 TO 3\n  PRINT i\nNEXT i"],
    "lolcode": ['VISIBLE "Hi"', "I HAS A x ITZ 5"],
    "z80": ["    LD A, 5\n    INC A\n    RET"],
    "shell": ['echo "hi"'],
    "sql": ["SELECT 1;"],
    "brainfood": ["++++++++[>++++<-]>."],
    "latin": ['dic "salve"', "x = 5", "Gallia est omnis divisa"],
    "klingon": ['jatlh "nuqneH"', "x = 5", "Qapla'"],
}


def build_cases():
    from squirrelator.translator import SUPPORTED

    langs = sorted(SUPPORTED)
    cases = []
    # Natural language to every language.
    for src in NATURAL:
        for frm in ("english", "pseudocode"):
            for to in langs:
                cases.append((src, frm, to))
    # Code to English, and code to every other language through English.
    for frm, sources in CODE.items():
        for src in sources:
            for to in langs:
                cases.append((src, frm, to))
    # Edges: unknown languages, names in odd case and spacing, padded input.
    cases += [
        ("print hello", "cobol", "python"),
        ("print hello", "english", "cobol"),
        ("print hello", "  English ", "PYTHON"),
        ("   print hello   \n", "english", "python"),
        ("", "english", "python"),
        ("", "python", "english"),
    ]
    return cases


def current(cases):
    return [{"source": s, "from": f, "to": t, "expected": translate(s, f, t)} for s, f, t in cases]


def load():
    if not GOLDEN.exists():
        return []
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", load(), ids=lambda c: f"{c['from'].strip()}->{c['to'].strip()}:{c['source'][:20]}")
def test_golden(case):
    assert translate(case["source"], case["from"], case["to"]) == case["expected"]


def test_golden_covers_every_case():
    """The file lists exactly the cases build_cases() makes, so a new
    language or pattern gets a golden entry instead of being skipped."""
    have = [(c["source"], c["from"], c["to"]) for c in load()]
    assert have == build_cases(), "run: python tests/test_golden.py --update"


def test_style_keyword_is_accepted():
    # Part of the public API that LanguageStudentDesk calls.
    assert translate("print hello", "english", "python", style="plain") == translate(
        "print hello", "english", "python"
    )


if __name__ == "__main__":
    if "--update" not in sys.argv:
        sys.exit("usage: python tests/test_golden.py --update")
    data = current(build_cases())
    GOLDEN.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(data)} cases to {GOLDEN}")
