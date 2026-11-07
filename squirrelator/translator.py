"""
Working rule-based translator for common patterns.
Supports human ↔ code and code ↔ code for a focused set of languages.
"""

import re
from dataclasses import replace
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
    engine: str = "auto",
) -> str:
    """Translate source and return the text.

    engine="rules" is the rule-based translator for code and a few phrases.
    engine="pipeline" runs the data-driven pipeline between
    squirrel-lang-data languages (squirrelator.pipeline.run); it is alpha.
    engine="auto" (the default) uses the pipeline for sentences between
    English, Latin and Klingon (rules only writes code comments for
    those), rules for every other pair rules supports, and the pipeline
    for a pair rules does not support but the pipeline does (japanese to
    english). When the pipeline understands none of the source, auto keeps
    the rules result.
    """
    from_lang = _norm(from_lang)
    to_lang = _norm(to_lang)
    text = source.strip()

    if engine == "auto" and _pipeline_first(from_lang, to_lang):
        return translate_full(source, from_lang, to_lang, style=style).text
    explained = _code_in_language(text, from_lang, to_lang)
    if explained is not None:
        return explained
    if _engine_for(engine, from_lang, to_lang) == "pipeline":
        from .pipeline import run
        try:
            return run(source, from_lang, to_lang).text
        except UnsupportedLanguage as e:
            return f"Unsupported language: {e.lang}\nSupported: {', '.join(e.supported)}"
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


ENGINES = ("auto", "rules", "pipeline")


# Human languages both engines know. Between them, auto uses the pipeline
# when Latin or Klingon is one side: rules only writes code comments there.
HUMAN = ("english", "latin", "klingon")
PIPELINE_FIRST = ("latin", "klingon")


def _pipeline_first(from_lang: str, to_lang: str) -> bool:
    """Whether auto sends this pair to the pipeline although rules supports
    it: sentences between English, Latin and Klingon, with Latin or Klingon
    on one side. Code pairs (latin to python) stay on rules."""
    return (from_lang != to_lang and from_lang in HUMAN and to_lang in HUMAN
            and (from_lang in PIPELINE_FIRST or to_lang in PIPELINE_FIRST)
            and _pipeline_knows(from_lang, to_lang))


def _engine_for(engine: str, from_lang: str, to_lang: str) -> str:
    """The engine that translates this pair: "rules" or "pipeline". auto
    gives the pipeline the English, Latin and Klingon pairs it translates
    as sentences, keeps every other pair rules supports on rules, and gives
    the pipeline pairs rules would reject. Without the language data, auto
    is rules."""
    if engine not in ENGINES:
        raise ValueError(f'engine must be one of {", ".join(ENGINES)}, not {engine!r}')
    if engine != "auto":
        return engine
    if from_lang in SUPPORTED and to_lang in SUPPORTED:
        return "pipeline" if _pipeline_first(from_lang, to_lang) else "rules"
    return "pipeline" if _pipeline_knows(from_lang, to_lang) else "rules"


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
    return "\n".join(e for _, e, _, _ in explanations)


def _with_literal(sentence: str, literal: str | None) -> str:
    """The code-pack row, then a quoted string or identifier left as written.
    The literal is not part of the sentence the pipeline translates."""
    if not literal:
        return sentence
    return f"{sentence}\n{literal}"


def _printed(inner: str) -> tuple[str, str]:
    """A print argument: a quoted string is "Print the word.", anything else
    is "Show the number." The argument itself is returned unchanged."""
    quoted = len(inner) >= 2 and inner[0] == inner[-1] and inner[0] in "\"'"
    sentence = "Print the word." if quoted else "Show the number."
    return _with_literal(sentence, inner), f"Print {inner}"


def _explain_lines(text: str, from_lang: str) -> list[tuple[str, str, bool, str]]:
    """Return (source line, explanation, understood, code gloss) for each line.

    The explanation is a code-pack row from squirrel-lang-data ("Print the
    word."), with a quoted string or identifier kept on the next line.
    understood is False where the explanation only repeats the line. The
    code gloss is the older wording code-to-code matches, so the literal
    stays the message instead of the row's nouns."""
    lines = text.splitlines()
    explanations = []

    def add(source: str, display: str, ok: bool, gloss: str | None = None):
        explanations.append((source, display, ok, gloss if gloss is not None else display))

    for line in lines:
        s = line.strip()
        if not s or s.startswith("#") or s.startswith(";"):
            continue

        if from_lang == "python":
            if s.startswith("print(") and s.endswith(")"):
                display, gloss = _printed(s[6:-1])
                add(s, display, True, gloss)
            elif "for " in s and " in " in s:
                add(s, "Start a loop.", True, "Start a loop")
            elif "=" in s and not s.startswith("if"):
                add(s, _with_literal("Set the value.", s), True, f"Assign a value: {s}")

        elif from_lang == "quickbasic":
            if s.upper().startswith("PRINT"):
                display, gloss = _printed(s[5:].strip())
                add(s, display, True, gloss)
            elif s.upper().startswith("FOR"):
                add(s, _with_literal("Start a loop.", s), True, f"Start a counted loop: {s}")
            elif s.upper().startswith("NEXT"):
                add(s, "End the loop.", True, "End the loop")

        elif from_lang == "lolcode":
            if "VISIBLE" in s:
                rest = s.split("VISIBLE", 1)[1].strip()
                add(s, _with_literal("Print the word.", rest), True, f"Show {rest}")
            elif "I HAS A" in s:
                add(s, _with_literal("Create a variable.", s), True, f"Create a variable: {s}")

        elif from_lang == "z80":
            if "LD" in s.upper():
                add(s, _with_literal("Load the data.", s), True, f"Load data: {s}")
            elif "INC" in s.upper():
                add(s, _with_literal("Add one.", s), True, f"Increment: {s}")
            elif "RET" in s.upper():
                add(s, "Return the value.", True, "Return from subroutine")

        elif from_lang == "javascript":
            if "console.log" in s:
                add(s, _with_literal("Print the word on the screen.", s), True, f"Print to console: {s}")
            elif "for (" in s:
                add(s, "Start a loop.", True, "Start a for loop")

        elif from_lang == "latin":
            if "print" in s.lower() or "dic" in s.lower():
                quoted = re.search(r"""(['"])(.+?)\1""", s)
                literal = quoted.group(0) if quoted else None
                add(s, _with_literal("Print the word.", literal), True, "Print / say something")
            elif "=" in s:
                add(s, _with_literal("Set the value.", s), True, f"Assign: {s}")
            else:
                add(s, f"Latin statement: {s}", False)

        elif from_lang == "klingon":
            if "jatlh" in s.lower() or "print" in s.lower():
                quoted = re.search(r"""(['"])(.+?)\1""", s)
                literal = quoted.group(0) if quoted else None
                add(s, _with_literal("Print the word.", literal), True, "Speak / print")
            elif "=" in s:
                add(s, _with_literal("Set the value.", s), True, f"Assign: {s}")
            else:
                add(s, f"Klingon statement: {s}", False)

        else:
            add(s, f"Execute: {s}", False)

    return explanations


# Programming languages whose explanations are code-pack sentences. A
# human language with a matrix column then gets that sentence from the
# pipeline, and the quoted string or identifier is copied after it.
_CODE_LANGS = {"python", "javascript", "quickbasic", "lolcode", "z80", "sql", "shell", "brainfood"}


def _code_in_language(text: str, from_lang: str, to_lang: str) -> str | None:
    if from_lang not in _CODE_LANGS or to_lang in SUPPORTED or to_lang in ("english", "pseudocode"):
        return None
    if not _pipeline_knows("english", to_lang):
        return None
    rows = [display for _, display, ok, _ in _explain_lines(text, from_lang) if ok]
    if not rows:
        return None
    from .pipeline import run
    parts = []
    for display in rows:
        row, sep, literal = display.partition("\n")
        spoken = run(row, "english", to_lang).text
        parts.append(f"{spoken}\n{literal}" if sep else spoken)
    return "\n".join(parts)


def _code_in_language_full(source: str, from_lang: str, to_lang: str) -> Translation | None:
    text = _code_in_language(source.strip(), from_lang, to_lang)
    if text is None:
        return None
    from .pipeline import run
    steps = []
    for line, display, ok, _ in _explain_lines(source.strip(), from_lang):
        if not ok:
            continue
        row, sep, literal = display.partition("\n")
        spoken = run(row, "english", to_lang).text
        shown = f"{spoken}\n{literal}" if sep else spoken
        steps.append(Step(line, shown, "Explained with a code-pack sentence."))
    return Translation(text, (), tuple(steps), (), 1.0, True, from_lang, to_lang, engine="pipeline")


def _code_to_code(text: str, from_lang: str, to_lang: str) -> str:
    # Code-to-code still matches the gloss that carries the literal, so
    # "hi" stays "hi". The row sentence is only what a person reads.
    gloss = "\n".join(g for _, _, _, g in _explain_lines(text, from_lang))
    if not gloss:
        gloss = "(no recognizable statements)"
    if gloss.startswith("(") or "no recognizable" in gloss:
        return f"# Direct {from_lang} → {to_lang} not yet mapped\n# Intermediate: {gloss}"
    return _from_natural(gloss, to_lang)


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
    engine: str = "auto",
) -> Translation:
    """Translate and return a Translation: the text plus its alternatives,
    breakdown, unknown parts, confidence and alpha label.

    Unlike translate(), an unknown language raises UnsupportedLanguage.
    Every pair is alpha until it has a passing test set. engine works as
    in translate(). Under engine="auto", a pair of English, Latin and
    Klingon gives the pipeline's result, with the rules result as
    second_opinion when rules understood any of the source. When rules
    understood the source at least as well (a code instruction such as
    "print hello"), the rules result comes first, with the pipeline's as
    second_opinion when it understood any.
    """
    frm, to = _norm(from_lang), _norm(to_lang)
    if engine == "auto" and _pipeline_first(frm, to):
        from .pipeline import run
        piped = run(source, frm, to)
        rules = _rules_full(source, from_lang, to_lang, style=style)
        if piped.confidence == 0 or 0 < piped.confidence <= rules.confidence:
            # A code instruction ("print hello", jatlh "nuqneH"): rules
            # understood it at least as well, so rules stays first.
            return replace(rules, second_opinion=piped) if piped.confidence > 0 else rules
        return replace(piped, second_opinion=rules) if rules.confidence > 0 else piped
    if _engine_for(engine, frm, to) == "pipeline":
        from .pipeline import run
        return run(source, frm, to)
    explained = _code_in_language_full(source, frm, to)
    if explained is not None:
        return explained
    return _rules_full(source, from_lang, to_lang, style=style)


def _pipeline_knows(*langs: str) -> bool:
    from .data import DataNotFound
    from .pipeline import languages
    try:
        known = set(languages())
    except DataNotFound:
        return False
    return all(lang in known for lang in langs)


def _rules_full(source: str, from_lang: str, to_lang: str, *, style: Optional[str]) -> Translation:
    """translate_full() for the rules engine."""
    frm, to = _norm(from_lang), _norm(to_lang)
    for lang in (frm, to):
        if lang not in SUPPORTED:
            raise UnsupportedLanguage(lang, sorted(SUPPORTED))
    text = translate(source, from_lang, to_lang, style=style, engine="rules")
    src = source.strip()

    def result(breakdown=(), unknown=(), confidence=0.0, alpha=True):
        return Translation(text, (), tuple(breakdown), tuple(unknown), confidence, alpha, frm, to,
                           engine="rules")

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
    explained = [(line, expl) for line, expl, ok, _ in all_explained if ok]
    understood = {line for line, _ in explained}
    unknown = [ln for ln in lines if ln not in understood]
    share = len(explained) / len(lines) if lines else 0.0

    if to == "english":
        steps = [Step(line, expl, "Explained line by line.") for line, expl in explained]
        return result(steps, unknown, share)

    english = "\n".join(g for _, _, _, g in all_explained)
    pattern, _ = _match_natural(english, to) if explained else (None, "")
    if pattern is None:
        return result([Step(line, expl, "Explained in English first.") for line, expl in explained],
                      unknown or lines, 0.0)
    steps = [Step(line, expl, "Explained in English first.") for line, expl in explained]
    steps.append(Step(english, text, f"Then read as {_PATTERN_WHY[pattern]}."))
    return result(steps, unknown, share)
