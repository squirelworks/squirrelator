"""Intent grammar for English prose → structured actions (Phase 4).

parse_intent() turns a short English instruction into an Intent. Generators
read the Intent and emit code. The Rules engine's English→code path uses
this so the regex patterns and the generators stay in one place; later
intents (if/else, functions, …) grow here without new ad-hoc matchers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


Kind = Literal["output", "loop", "assignment"]


@dataclass(frozen=True)
class Intent:
    """One recognised English instruction."""

    kind: Kind
    # output: message text; loop: unused; assignment: variable name
    name: str = ""
    # output: unused; loop: start; assignment: value expression as written
    start: str = ""
    # loop: end inclusive
    end: str = ""


def parse_intent(text: str) -> Intent | None:
    """Parse a short English instruction into an Intent, or None."""
    t = text.strip().lower()
    if not t:
        return None

    m = re.search(r"(?:print|show|display|output)\s+['\"]?(.+?)['\"]?$", t)
    if m or "hello" in t:
        msg = m.group(1).strip("\"'") if m else "Hello"
        return Intent("output", name=msg)

    m = re.search(
        r"(?:for|loop|count|repeat).*?(?:from\s+)?(\d+)\s+(?:to|through)\s+(\d+)",
        t,
    )
    if m:
        return Intent("loop", start=m.group(1), end=m.group(2))

    m = re.search(r"(?:set|let|make)\s+(\w+)\s+(?:to|=)\s+(.+)", t)
    if m:
        return Intent("assignment", name=m.group(1), start=m.group(2).strip())

    return None


def generate(intent: Intent, to_lang: str) -> str | None:
    """Emit code for to_lang from intent, or None when that target has no mapping."""
    if intent.kind == "output":
        msg = intent.name
        rules = {
            "python": f'print("{msg}")',
            "javascript": f'console.log("{msg}");',
            "quickbasic": f'PRINT "{msg}"',
            "lolcode": f'VISIBLE "{msg}"',
            "brainfood": (
                "# brainFOOD Hello (simplified)\n"
                "++++++++++[>+++++++>++++++++++>+++>+<<<<-]>++.>+.+++++++..+++."
            ),
            "z80": (
                f'    ; print "{msg}" (conceptual)\n'
                f"    LD   HL, msg\n"
                f"    CALL print_string\n"
                f'msg: DEFM "{msg}"\n'
                f"     DEFB 0"
            ),
            "shell": f'echo "{msg}"',
            "sql": f"SELECT '{msg}' AS message;",
            "latin": f'# Latin: Salve / {msg}\nprint("{msg}")  # or: dic "{msg}"',
            "klingon": (
                f"# Klingon: {msg}\n"
                f'# tlhIngan Hol: jatlh "{msg}"\n'
                f'print("{msg}")'
            ),
        }
        return rules.get(to_lang)

    if intent.kind == "loop":
        start, end = intent.start, intent.end
        rules = {
            "python": f"for i in range({start}, {int(end)+1}):\n    print(i)",
            "javascript": (
                f"for (let i = {start}; i <= {end}; i++) {{\n"
                f"  console.log(i);\n}}"
            ),
            "quickbasic": f"FOR i = {start} TO {end}\n  PRINT i\nNEXT i",
            "lolcode": (
                f"IM IN YR loop UPPIN YR i TIL BOTH SAEM i AN {end}\n"
                f"  VISIBLE i\nIM OUTTA YR loop"
            ),
            "shell": f"for i in $(seq {start} {end}); do echo $i; done",
            "latin": (
                f"# Latin loop {start} to {end}\n"
                f"for i in range({start}, {int(end)+1}):\n"
                f"    print(i)  # numerus"
            ),
            "klingon": (
                f"# Klingon loop {start} to {end}\n"
                f"# wej (or appropriate number) logh\n"
                f"for i in range({start}, {int(end)+1}):\n"
                f"    print(i)"
            ),
        }
        return rules.get(to_lang)

    if intent.kind == "assignment":
        var, val = intent.name, intent.start
        rules = {
            "python": f"{var} = {val}",
            "javascript": f"let {var} = {val};",
            "quickbasic": f"{var} = {val}",
            "lolcode": f"I HAS A {var} ITZ {val}",
            "shell": f"{var}={val}",
            "latin": f"# Latin: {var} est {val}\n{var} = {val}",
            "klingon": f"# Klingon: {var} {val} 'oH\n{var} = {val}",
        }
        return rules.get(to_lang)

    return None
