"""
Working rule-based translator for common patterns.
Supports human ↔ code and code ↔ code for a focused set of languages.
"""

import re
from typing import Optional

from .result import Step, Translation, UnsupportedLanguage

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
    engine: str = "rules",
) -> str:
    """Translate source and return the text.

    engine="rules" (the default) is the rule-based translator for code and
    a few phrases. engine="pipeline" runs the data-driven pipeline between
    squirrel-lang-data languages (squirrelator.pipeline.run); it is alpha.
    """
    from_lang = _norm(from_lang)
    to_lang = _norm(to_lang)
    text = source.strip()

    if engine == "pipeline":
        from .pipeline import run
        try:
            return run(source, from_lang, to_lang).text
        except UnsupportedLanguage as e:
            return f"Unsupported language: {e.lang}\nSupported: {', '.join(e.supported)}"
    _check_engine(engine)

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


def _check_engine(engine: str) -> None:
    if engine not in ("rules", "pipeline"):
        raise ValueError(f'engine must be "rules" or "pipeline", not {engine!r}')


def _from_natural(text: str, to_lang: str) -> str:
    return _match_natural(text, to_lang)[1]


def _match_natural(text: str, to_lang: str) -> tuple[str | None, str]:
    """Return (pattern, output). pattern names the rule that matched in plain
    words, or is None when no rule produced code for to_lang."""
    t = text.lower()

    # print / show / display
    m = re.search(r"(?:print|show|display|output)\s+['\"]?(.+?)['\"]?$", t)
    if m or "hello" in t:
        msg = m.group(1).strip("\"'") if m else "Hello"
        rules = {
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
        }
        if to_lang in rules:
            return "output", rules[to_lang]
        return None, f"# no mapping for {to_lang}"

    # loop 1 to N / count to N
    m = re.search(r"(?:for|loop|count|repeat).*?(?:from\s+)?(\d+)\s+(?:to|through)\s+(\d+)", t)
    if m:
        start, end = m.group(1), m.group(2)
        rules = {
            "python": f"for i in range({start}, {int(end)+1}):\n    print(i)",
            "javascript": f"for (let i = {start}; i <= {end}; i++) {{\n  console.log(i);\n}}",
            "quickbasic": f"FOR i = {start} TO {end}\n  PRINT i\nNEXT i",
            "lolcode": f"IM IN YR loop UPPIN YR i TIL BOTH SAEM i AN {end}\n  VISIBLE i\nIM OUTTA YR loop",
            "shell": f"for i in $(seq {start} {end}); do echo $i; done",
            "latin": f"# Latin loop {start} to {end}\nfor i in range({start}, {int(end)+1}):\n    print(i)  # numerus",
            "klingon": f"# Klingon loop {start} to {end}\n# wej (or appropriate number) logh\nfor i in range({start}, {int(end)+1}):\n    print(i)",
        }
        if to_lang in rules:
            return "loop", rules[to_lang]
        return None, f"# no loop mapping for {to_lang}"

    # variable assignment
    m = re.search(r"(?:set|let|make)\s+(\w+)\s+(?:to|=)\s+(.+)", t)
    if m:
        var, val = m.group(1), m.group(2).strip()
        rules = {
            "python": f"{var} = {val}",
            "javascript": f"let {var} = {val};",
            "quickbasic": f"{var} = {val}",
            "lolcode": f"I HAS A {var} ITZ {val}",
            "shell": f"{var}={val}",
            "latin": f"# Latin: {var} est {val}\n{var} = {val}",
            "klingon": f"# Klingon: {var} {val} 'oH\n{var} = {val}",
        }
        if to_lang in rules:
            return "assignment", rules[to_lang]
        return None, f"# no assignment mapping for {to_lang}"

    return None, f"# Could not match a known pattern for {to_lang}\n# Source: {text}"


def _to_english(text: str, from_lang: str) -> str:
    explanations = _explain_lines(text, from_lang)
    if not explanations:
        return "(no recognizable statements)"
    return "\n".join(e for _, e, _ in explanations)


def _explain_lines(text: str, from_lang: str) -> list[tuple[str, str, bool]]:
    """Return (source line, plain-English explanation, understood) for each
    line. understood is False where the explanation only repeats the line."""
    lines = text.splitlines()
    explanations = []

    for line in lines:
        s = line.strip()
        if not s or s.startswith("#") or s.startswith(";"):
            continue

        if from_lang == "python":
            if s.startswith("print("):
                explanations.append((s, f"Print {s[6:-1]}", True))
            elif "for " in s and " in " in s:
                explanations.append((s, "Start a loop", True))
            elif "=" in s and not s.startswith("if"):
                explanations.append((s, f"Assign a value: {s}", True))

        elif from_lang == "quickbasic":
            if s.upper().startswith("PRINT"):
                explanations.append((s, f"Print {s[5:].strip()}", True))
            elif s.upper().startswith("FOR"):
                explanations.append((s, f"Start a counted loop: {s}", True))
            elif s.upper().startswith("NEXT"):
                explanations.append((s, "End the loop", True))

        elif from_lang == "lolcode":
            if "VISIBLE" in s:
                explanations.append((s, f"Show {s.split('VISIBLE',1)[1].strip()}", True))
            elif "I HAS A" in s:
                explanations.append((s, f"Create a variable: {s}", True))

        elif from_lang == "z80":
            if "LD" in s.upper():
                explanations.append((s, f"Load data: {s}", True))
            elif "INC" in s.upper():
                explanations.append((s, f"Increment: {s}", True))
            elif "RET" in s.upper():
                explanations.append((s, "Return from subroutine", True))

        elif from_lang == "javascript":
            if "console.log" in s:
                explanations.append((s, f"Print to console: {s}", True))
            elif "for (" in s:
                explanations.append((s, "Start a for loop", True))

        elif from_lang == "latin":
            if "print" in s.lower() or "dic" in s.lower():
                explanations.append((s, "Print / say something", True))
            elif "=" in s:
                explanations.append((s, f"Assign: {s}", True))
            else:
                explanations.append((s, f"Latin statement: {s}", False))

        elif from_lang == "klingon":
            if "jatlh" in s.lower() or "print" in s.lower():
                explanations.append((s, "Speak / print", True))
            elif "=" in s:
                explanations.append((s, f"Assign: {s}", True))
            else:
                explanations.append((s, f"Klingon statement: {s}", False))

        else:
            explanations.append((s, f"Execute: {s}", False))

    return explanations


def _code_to_code(text: str, from_lang: str, to_lang: str) -> str:
    # Simple pass-through via English intermediate for known patterns
    english = _to_english(text, from_lang)
    if english.startswith("(") or "no recognizable" in english:
        return f"# Direct {from_lang} → {to_lang} not yet mapped\n# Intermediate: {english}"
    return _from_natural(english, to_lang)


# Plain-words names for the patterns _match_natural knows.
_PATTERN_WHY = {
    "output": "an instruction to print or show something",
    "loop": "a loop counting from one number to another",
    "assignment": "setting a variable to a value",
}


def translate_full(
    source: str,
    from_lang: str,
    to_lang: str,
    *,
    style: Optional[str] = None,
    engine: str = "rules",
) -> Translation:
    """Translate and return a Translation: the text plus its alternatives,
    breakdown, unknown parts, confidence and alpha label.

    Unlike translate(), an unknown language raises UnsupportedLanguage.
    Every pair is alpha until it has a passing test set. engine works as
    in translate().
    """
    frm, to = _norm(from_lang), _norm(to_lang)
    if engine == "pipeline":
        from .pipeline import run
        return run(source, frm, to)
    _check_engine(engine)
    for lang in (frm, to):
        if lang not in SUPPORTED:
            raise UnsupportedLanguage(lang, sorted(SUPPORTED))
    text = translate(source, from_lang, to_lang, style=style)
    src = source.strip()

    def result(breakdown=(), unknown=(), confidence=0.0, alpha=True):
        return Translation(text, (), tuple(breakdown), tuple(unknown), confidence, alpha, frm, to)

    if frm == to:
        return result(confidence=1.0, alpha=False)

    if frm in ("english", "pseudocode"):
        pattern, _ = _match_natural(src, to)
        if pattern is None:
            return result(unknown=[src] if src else [])
        return result([Step(src, text, f"Read as {_PATTERN_WHY[pattern]}.")], confidence=1.0)

    lines = [ln.strip() for ln in src.splitlines()]
    lines = [ln for ln in lines if ln and not ln.startswith(("#", ";"))]
    all_explained = _explain_lines(src, frm)
    explained = [(line, expl) for line, expl, ok in all_explained if ok]
    understood = {line for line, _ in explained}
    unknown = [ln for ln in lines if ln not in understood]
    share = len(explained) / len(lines) if lines else 0.0

    if to == "english":
        steps = [Step(line, expl, "Explained line by line.") for line, expl in explained]
        return result(steps, unknown, share)

    english = "\n".join(e for _, e, _ in all_explained)
    pattern, _ = _match_natural(english, to) if explained else (None, "")
    if pattern is None:
        return result([Step(line, expl, "Explained in English first.") for line, expl in explained],
                      unknown or lines, 0.0)
    steps = [Step(line, expl, "Explained in English first.") for line, expl in explained]
    steps.append(Step(english, text, f"Then read as {_PATTERN_WHY[pattern]}."))
    return result(steps, unknown, share)
