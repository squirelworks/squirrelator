"""
Working rule-based translator for common patterns.
Supports human ↔ code and code ↔ code for a focused set of languages.
"""

import re
from typing import Optional

SUPPORTED = {
    "english", "pseudocode", "python", "javascript", "quickbasic",
    "brainfood", "lolcode", "z80", "sql", "shell",
    "latin", "klingon"
}

def _norm(s: str) -> str:
    return s.strip().lower()

def translate(
    source: str,
    from_lang: str,
    to_lang: str,
    *,
    style: Optional[str] = None,
) -> str:
    from_lang = _norm(from_lang)
    to_lang = _norm(to_lang)
    text = source.strip()

    if from_lang not in SUPPORTED or to_lang not in SUPPORTED:
        return (
            f"Unsupported language pair: {from_lang} → {to_lang}\n"
            f"Supported: {', '.join(sorted(SUPPORTED))}"
        )

    if from_lang == to_lang:
        return text

    # English / pseudocode → code
    if from_lang in ("english", "pseudocode"):
        return _from_natural(text, to_lang)

    # Code → English
    if to_lang == "english":
        return _to_english(text, from_lang)

    # Code → code (via simple pattern mapping)
    return _code_to_code(text, from_lang, to_lang)


def _from_natural(text: str, to_lang: str) -> str:
    t = text.lower()

    # print / show / display
    m = re.search(r"(?:print|show|display|output)\s+['\"]?(.+?)['\"]?$", t)
    if m or "hello" in t:
        msg = m.group(1).strip("\"'") if m else "Hello"
        return {
            "python": f'print("{msg}")',
            "javascript": f'console.log("{msg}");',
            "quickbasic": f'PRINT "{msg}"',
            "lolcode": f'VISIBLE "{msg}"',
            "brainfood": "# brainFOOD Hello (simplified)\n++++++++++[>+++++++>++++++++++>+++>+<<<<-]>++.>+.+++++++..+++.",
            "z80": f"    ; print \"{msg}\" (conceptual)\n    LD   HL, msg\n    CALL print_string\nmsg: DEFM \"{msg}\"\n     DEFB 0",
            "shell": f'echo "{msg}"',
            "sql": f"SELECT '{msg}' AS message;",
            "latin": f"# Latin: Salve / {msg}\nprint(\"{msg}\")  # or: dic \"{msg}\"",
            "klingon": f"# Klingon: {msg}\n# tlhIngan Hol: jatlh \"{msg}\"\nprint(\"{msg}\")",
        }.get(to_lang, f"# no mapping for {to_lang}")

    # loop 1 to N / count to N
    m = re.search(r"(?:for|loop|count|repeat).*?(?:from\s+)?(\d+)\s+(?:to|through)\s+(\d+)", t)
    if m:
        start, end = m.group(1), m.group(2)
        return {
            "python": f"for i in range({start}, {int(end)+1}):\n    print(i)",
            "javascript": f"for (let i = {start}; i <= {end}; i++) {{\n  console.log(i);\n}}",
            "quickbasic": f"FOR i = {start} TO {end}\n  PRINT i\nNEXT i",
            "lolcode": f"IM IN YR loop UPPIN YR i TIL BOTH SAEM i AN {end}\n  VISIBLE i\nIM OUTTA YR loop",
            "shell": f"for i in $(seq {start} {end}); do echo $i; done",
            "latin": f"# Latin loop {start} to {end}\nfor i in range({start}, {int(end)+1}):\n    print(i)  # numerus",
            "klingon": f"# Klingon loop {start} to {end}\n# wej (or appropriate number) logh\nfor i in range({start}, {int(end)+1}):\n    print(i)",
        }.get(to_lang, f"# no loop mapping for {to_lang}")

    # variable assignment
    m = re.search(r"(?:set|let|make)\s+(\w+)\s+(?:to|=)\s+(.+)", t)
    if m:
        var, val = m.group(1), m.group(2).strip()
        return {
            "python": f"{var} = {val}",
            "javascript": f"let {var} = {val};",
            "quickbasic": f"{var} = {val}",
            "lolcode": f"I HAS A {var} ITZ {val}",
            "shell": f"{var}={val}",
            "latin": f"# Latin: {var} est {val}\n{var} = {val}",
            "klingon": f"# Klingon: {var} {val} 'oH\n{var} = {val}",
        }.get(to_lang, f"# no assignment mapping for {to_lang}")

    return f"# Could not match a known pattern for {to_lang}\n# Source: {text}"


def _to_english(text: str, from_lang: str) -> str:
    lines = text.splitlines()
    explanations = []

    for line in lines:
        s = line.strip()
        if not s or s.startswith("#") or s.startswith(";"):
            continue

        if from_lang == "python":
            if s.startswith("print("):
                explanations.append(f"Print {s[6:-1]}")
            elif "for " in s and " in " in s:
                explanations.append("Start a loop")
            elif "=" in s and not s.startswith("if"):
                explanations.append(f"Assign a value: {s}")

        elif from_lang == "quickbasic":
            if s.upper().startswith("PRINT"):
                explanations.append(f"Print {s[5:].strip()}")
            elif s.upper().startswith("FOR"):
                explanations.append(f"Start a counted loop: {s}")
            elif s.upper().startswith("NEXT"):
                explanations.append("End the loop")

        elif from_lang == "lolcode":
            if "VISIBLE" in s:
                explanations.append(f"Show {s.split('VISIBLE',1)[1].strip()}")
            elif "I HAS A" in s:
                explanations.append(f"Create a variable: {s}")

        elif from_lang == "z80":
            if "LD" in s.upper():
                explanations.append(f"Load data: {s}")
            elif "INC" in s.upper():
                explanations.append(f"Increment: {s}")
            elif "RET" in s.upper():
                explanations.append("Return from subroutine")

        elif from_lang == "javascript":
            if "console.log" in s:
                explanations.append(f"Print to console: {s}")
            elif "for (" in s:
                explanations.append("Start a for loop")

        elif from_lang == "latin":
            if "print" in s.lower() or "dic" in s.lower():
                explanations.append("Print / say something")
            elif "=" in s:
                explanations.append(f"Assign: {s}")
            else:
                explanations.append(f"Latin statement: {s}")

        elif from_lang == "klingon":
            if "jatlh" in s.lower() or "print" in s.lower():
                explanations.append("Speak / print")
            elif "=" in s:
                explanations.append(f"Assign: {s}")
            else:
                explanations.append(f"Klingon statement: {s}")

        else:
            explanations.append(f"Execute: {s}")

    if not explanations:
        return "(no recognizable statements)"
    return "\n".join(explanations)


def _code_to_code(text: str, from_lang: str, to_lang: str) -> str:
    # Simple pass-through via English intermediate for known patterns
    english = _to_english(text, from_lang)
    if english.startswith("(") or "no recognizable" in english:
        return f"# Direct {from_lang} → {to_lang} not yet mapped\n# Intermediate: {english}"
    return _from_natural(english, to_lang)
