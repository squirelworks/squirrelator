"""Intent grammar for English prose → structured actions (Phase 4).

parse_intent() turns a short English instruction into an Intent. Generators
read the Intent and emit code. The Rules engine's English→code path uses
this so the regex patterns and the generators stay in one place; later
intents (functions, lists, …) grow here without new ad-hoc matchers.
if→print already supports an optional else→print branch via Intent.alt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


Kind = Literal["output", "loop", "assignment", "if"]

_OPS = {
    ">": ">",
    ">=": ">=",
    "<": "<",
    "<=": "<=",
    "=": "==",
    "==": "==",
    "!=": "!=",
    "greater than": ">",
    "less than": "<",
    "equal to": "==",
    "equals": "==",
}


@dataclass(frozen=True)
class Intent:
    """One recognised English instruction."""

    kind: Kind
    # output: message; loop: unused; assignment/if: variable name
    name: str = ""
    # loop: start; assignment: value; if: comparison operator
    start: str = ""
    # loop: end; if: compare value
    end: str = ""
    # if: then-branch (usually output)
    body: Intent | None = None
    # if: else-branch (usually output)
    alt: Intent | None = None


def parse_intent(text: str) -> Intent | None:
    """Parse a short English instruction into an Intent, or None."""
    t = text.strip().lower()
    if not t:
        return None

    # if x > 5 print hi else print bye  /  if x is greater than 5 then print hi else print bye
    m = re.search(
        r"if\s+(\w+)\s*(>=|<=|==|!=|>|<|=)\s*(\S+)\s+"
        r"(?:then\s+)?(?:print|show|display|output)\s+['\"]?(.+?)['\"]?\s+"
        r"else\s+(?:print|show|display|output)\s+['\"]?(.+?)['\"]?$",
        t,
    )
    if not m:
        m = re.search(
            r"if\s+(\w+)\s+is\s+(greater than|less than|equal to|equals)\s+(\S+)\s+"
            r"(?:then\s+)?(?:print|show|display|output)\s+['\"]?(.+?)['\"]?\s+"
            r"else\s+(?:print|show|display|output)\s+['\"]?(.+?)['\"]?$",
            t,
        )
    if m:
        op = _OPS[m.group(2)]
        return Intent(
            "if",
            name=m.group(1),
            start=op,
            end=m.group(3).strip("\"'"),
            body=Intent("output", name=m.group(4).strip("\"'")),
            alt=Intent("output", name=m.group(5).strip("\"'")),
        )

    # if x > 5 print hi  /  if x is greater than 5 then print hi
    m = re.search(
        r"if\s+(\w+)\s*(>=|<=|==|!=|>|<|=)\s*(\S+)\s+"
        r"(?:then\s+)?(?:print|show|display|output)\s+['\"]?(.+?)['\"]?$",
        t,
    )
    if not m:
        m = re.search(
            r"if\s+(\w+)\s+is\s+(greater than|less than|equal to|equals)\s+(\S+)\s+"
            r"(?:then\s+)?(?:print|show|display|output)\s+['\"]?(.+?)['\"]?$",
            t,
        )
    if m:
        op = _OPS[m.group(2)]
        return Intent(
            "if",
            name=m.group(1),
            start=op,
            end=m.group(3).strip("\"'"),
            body=Intent("output", name=m.group(4).strip("\"'")),
        )

    m = re.search(r"(?:print|show|display|output)\s+['\"]?(.+?)['\"]?$", t)
    if m or ("hello" in t and not t.startswith("if ")):
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

    if intent.kind == "if" and intent.body is not None:
        var, op, val = intent.name, intent.start, intent.end
        then = generate(intent.body, to_lang)
        if then is None:
            return None
        then_lines = then.splitlines()
        else_code = generate(intent.alt, to_lang) if intent.alt is not None else None
        else_lines = else_code.splitlines() if else_code else None
        if to_lang == "python":
            body = "\n".join(f"    {ln}" for ln in then_lines)
            out = f"if {var} {op} {val}:\n{body}"
            if else_lines is not None:
                alt = "\n".join(f"    {ln}" for ln in else_lines)
                out += f"\nelse:\n{alt}"
            return out
        if to_lang == "javascript":
            body = "\n".join(f"  {ln}" for ln in then_lines)
            out = f"if ({var} {op} {val}) {{\n{body}\n}}"
            if else_lines is not None:
                alt = "\n".join(f"  {ln}" for ln in else_lines)
                out += f" else {{\n{alt}\n}}"
            return out
        if to_lang == "quickbasic":
            body = "\n".join(f"  {ln}" for ln in then_lines)
            if else_lines is not None:
                alt = "\n".join(f"  {ln}" for ln in else_lines)
                return f"IF {var} {op} {val} THEN\n{body}\nELSE\n{alt}\nEND IF"
            return f"IF {var} {op} {val} THEN\n{body}\nEND IF"
        if to_lang == "shell":
            body = "\n".join(f"  {ln}" for ln in then_lines)
            sh_ops = {">": "-gt", ">=": "-ge", "<": "-lt", "<=": "-le", "==": "-eq", "!=": "-ne"}
            sh_op = sh_ops.get(op)
            if sh_op is None:
                return None
            out = f'if [ "${var}" {sh_op} {val} ]; then\n{body}'
            if else_lines is not None:
                alt = "\n".join(f"  {ln}" for ln in else_lines)
                out += f"\nelse\n{alt}"
            return out + "\nfi"
        return None

    return None
