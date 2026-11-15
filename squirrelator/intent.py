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


Kind = Literal[
    "output",
    "loop",
    "assignment",
    "if",
    "input",
    "function",
    "call",
    "list",
    "map",
    "file",
]

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
    # output: message; loop: unused; assignment/if/input/function: name
    name: str = ""
    # loop: start; assignment: value; if: comparison operator
    start: str = ""
    # loop: end; if: compare value
    end: str = ""
    # if/function: then-branch or body (usually output)
    body: Intent | None = None
    # if: else-branch (usually output)
    alt: Intent | None = None


def _parse_map_pairs(raw: str) -> list[tuple[str, str]]:
    """Parse 'alice 30 bob 40' or 'alice:30, bob:85' into (key, value) pairs."""
    tagged = re.findall(r"(\w+)\s*[=:]\s*([^\s,]+)", raw)
    if tagged:
        return [(k, v.strip("\"'")) for k, v in tagged]
    toks = [p.strip("\"'") for p in re.split(r"\s+", raw) if p.strip("\"'")]
    if len(toks) >= 2 and len(toks) % 2 == 0:
        return [(toks[i], toks[i + 1]) for i in range(0, len(toks), 2)]
    return []


def parse_intent(text: str) -> Intent | None:
    """Parse a short English instruction into an Intent, or None."""
    t = text.strip().lower()
    if not t:
        return None

    # define a function greet that prints hello
    m = re.search(
        r"(?:define|create|make)\s+(?:a\s+)?(?:function|def|procedure)\s+(\w+)\s+"
        r"that\s+(?:prints?|shows?|displays?|outputs?)\s+['\"]?(.+?)['\"]?$",
        t,
    )
    if m:
        return Intent(
            "function",
            name=m.group(1),
            body=Intent("output", name=m.group(2).strip("\"'")),
        )

    # call greet  /  run the function greet  /  invoke sayhi
    m = re.search(
        r"(?:call|run|invoke)\s+(?:the\s+)?(?:function\s+)?(\w+)$",
        t,
    )
    if m and m.group(1) not in {"the", "a", "an", "function"}:
        return Intent("call", name=m.group(1))

    # make a list called items with a, b, c  /  create list nums of 1 2 3
    m = re.search(
        r"(?:make|create|define)\s+(?:a\s+)?list\s+(?:called\s+|named\s+)?(\w+)\s+"
        r"(?:with|of|:)\s+(.+)$",
        t,
    )
    if m:
        raw = m.group(2).strip()
        parts = [p.strip("\"'") for p in re.split(r"\s*,\s*|\s+", raw) if p.strip("\"'")]
        if parts:
            return Intent("list", name=m.group(1), start=",".join(parts))

    # make a map called ages with alice 30 bob 40  /  create dictionary scores of math:90, english:85
    m = re.search(
        r"(?:make|create|define)\s+(?:a\s+)?(?:map|dict|dictionary)\s+"
        r"(?:called\s+|named\s+)?(\w+)\s+(?:with|of|:)\s+(.+)$",
        t,
    )
    if m:
        pairs = _parse_map_pairs(m.group(2).strip())
        if pairs:
            return Intent(
                "map",
                name=m.group(1),
                start=";".join(f"{k}={v}" for k, v in pairs),
            )

    # read file data.txt [into text]  /  write hello to file out.txt
    m = re.search(
        r"read\s+(?:from\s+)?(?:the\s+)?file\s+(\S+)(?:\s+into\s+(\w+))?$",
        t,
    )
    if m:
        return Intent("file", name=m.group(1).strip("\"'"), start="read", end=m.group(2) or "text")
    m = re.search(
        r"write\s+(.+?)\s+to\s+(?:the\s+)?file\s+(\S+)$",
        t,
    )
    if m:
        return Intent(
            "file",
            name=m.group(2).strip("\"'"),
            start="write",
            end=m.group(1).strip("\"'"),
        )
    m = re.search(
        r"write\s+(?:to\s+)?(?:the\s+)?file\s+(\S+)\s+(?:with|:)\s+(.+)$",
        t,
    )
    if m:
        return Intent(
            "file",
            name=m.group(1).strip("\"'"),
            start="write",
            end=m.group(2).strip("\"'"),
        )

    # ask for name / ask the user for name / input name / read name from the user
    m = re.search(
        r"(?:ask(?:\s+the\s+user)?\s+for|input|read|get)\s+(\w+)"
        r"(?:\s+from\s+(?:the\s+)?user)?$",
        t,
    )
    if m and m.group(1) not in {"for", "the", "a", "an", "user"}:
        return Intent("input", name=m.group(1))

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
        return Intent(
            "assignment", name=m.group(1), start=_normalize_arith(m.group(2).strip())
        )

    return None


def _normalize_arith(expr: str) -> str:
    """Turn English arithmetic words into + - * / operators."""
    expr = re.sub(r"\s+plus\s+", " + ", expr)
    expr = re.sub(r"\s+minus\s+", " - ", expr)
    expr = re.sub(r"\s+(?:times|multiplied by)\s+", " * ", expr)
    expr = re.sub(r"\s+divided by\s+", " / ", expr)
    return re.sub(r"\s+", " ", expr).strip()


def generate(intent: Intent, to_lang: str) -> str | None:
    """Emit code for to_lang from intent, or None when that target has no mapping."""
    if intent.kind == "output":
        msg = intent.name
        rules = {
            "python": f'print("{msg}")',
            "javascript": f'console.log("{msg}");',
            "c": f'printf("{msg}\\n");',
            "cpp": f'std::cout << "{msg}" << std::endl;',
            "csharp": f'Console.WriteLine("{msg}");',
            "java": f'System.out.println("{msg}");',
            "rust": f'println!("{msg}");',
            "go": f'fmt.Println("{msg}")',
            "kotlin": f'println("{msg}")',
            "swift": f'print("{msg}")',
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
            "c": (
                f"for (int i = {start}; i <= {end}; i++) {{\n"
                f'  printf("%d\\n", i);\n}}'
            ),
            "cpp": (
                f"for (int i = {start}; i <= {end}; i++) {{\n"
                f"  std::cout << i << std::endl;\n}}"
            ),
            "csharp": (
                f"for (int i = {start}; i <= {end}; i++) {{\n"
                f"  Console.WriteLine(i);\n}}"
            ),
            "java": (
                f"for (int i = {start}; i <= {end}; i++) {{\n"
                f"  System.out.println(i);\n}}"
            ),
            "rust": (
                f"for i in {start}..={end} {{\n"
                f"  println!(\"{{}}\", i);\n}}"
            ),
            "go": (
                f"for i := {start}; i <= {end}; i++ {{\n"
                f"  fmt.Println(i)\n}}"
            ),
            "kotlin": (
                f"for (i in {start}..{end}) {{\n"
                f"  println(i)\n}}"
            ),
            "swift": (
                f"for i in {start}...{end} {{\n"
                f"  print(i)\n}}"
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
            "c": _c_assignment(var, val),
            "cpp": _cpp_assignment(var, val),
            "csharp": _csharp_assignment(var, val),
            "java": _java_assignment(var, val),
            "rust": _rust_assignment(var, val),
            "go": _go_assignment(var, val),
            "kotlin": _kotlin_assignment(var, val),
            "swift": _swift_assignment(var, val),
            "quickbasic": f"{var} = {val}",
            "lolcode": f"I HAS A {var} ITZ {val}",
            "shell": f"{var}={val}",
            "latin": f"# Latin: {var} est {val}\n{var} = {val}",
            "klingon": f"# Klingon: {var} {val} 'oH\n{var} = {val}",
        }
        return rules.get(to_lang)

    if intent.kind == "input":
        var = intent.name
        rules = {
            "python": f'{var} = input()',
            "javascript": f'let {var} = prompt();',
            "c": f'int {var};\nscanf("%d", &{var});',
            "cpp": f"int {var};\nstd::cin >> {var};",
            "csharp": f"int {var} = int.Parse(Console.ReadLine());",
            "java": f"int {var} = new java.util.Scanner(System.in).nextInt();",
            "rust": f"let mut {var} = String::new();\nstd::io::stdin().read_line(&mut {var}).unwrap();",
            "go": f"var {var} int\nfmt.Scan(&{var})",
            "kotlin": f"val {var} = readln()",
            "swift": f'let {var} = readLine() ?? ""',
            "quickbasic": f"INPUT {var}",
            "lolcode": f"GIMMEH {var}",
            "shell": f"read {var}",
            "latin": f'# Latin: lege {var}\n{var} = input()',
            "klingon": f"# Klingon: yIlaD {var}\n{var} = input()",
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
        if to_lang in ("c", "cpp", "csharp", "java", "rust", "go", "kotlin", "swift"):
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

    if intent.kind == "function" and intent.body is not None:
        fname = intent.name
        body_code = generate(intent.body, to_lang)
        if body_code is None:
            return None
        body_lines = body_code.splitlines()
        if to_lang == "python":
            body = "\n".join(f"    {ln}" for ln in body_lines)
            return f"def {fname}():\n{body}"
        if to_lang == "javascript":
            body = "\n".join(f"  {ln}" for ln in body_lines)
            return f"function {fname}() {{\n{body}\n}}"
        if to_lang == "c":
            body = "\n".join(f"  {ln}" for ln in body_lines)
            return f"void {fname}(void) {{\n{body}\n}}"
        if to_lang == "cpp":
            body = "\n".join(f"  {ln}" for ln in body_lines)
            return f"void {fname}() {{\n{body}\n}}"
        if to_lang == "csharp":
            body = "\n".join(f"  {ln}" for ln in body_lines)
            return f"void {fname}() {{\n{body}\n}}"
        if to_lang == "java":
            body = "\n".join(f"  {ln}" for ln in body_lines)
            return f"void {fname}() {{\n{body}\n}}"
        if to_lang == "rust":
            body = "\n".join(f"  {ln}" for ln in body_lines)
            return f"fn {fname}() {{\n{body}\n}}"
        if to_lang == "go":
            body = "\n".join(f"  {ln}" for ln in body_lines)
            return f"func {fname}() {{\n{body}\n}}"
        if to_lang == "kotlin":
            body = "\n".join(f"  {ln}" for ln in body_lines)
            return f"fun {fname}() {{\n{body}\n}}"
        if to_lang == "swift":
            body = "\n".join(f"  {ln}" for ln in body_lines)
            return f"func {fname}() {{\n{body}\n}}"
        if to_lang == "quickbasic":
            body = "\n".join(f"  {ln}" for ln in body_lines)
            return f"SUB {fname}\n{body}\nEND SUB"
        if to_lang == "shell":
            body = "\n".join(f"  {ln}" for ln in body_lines)
            return f"{fname}() {{\n{body}\n}}"
        if to_lang == "lolcode":
            body = "\n".join(f"  {ln}" for ln in body_lines)
            return f"HOW IZ I {fname}\n{body}\nIF U SAY SO"
        return None

    if intent.kind == "call":
        fname = intent.name
        rules = {
            "python": f"{fname}()",
            "javascript": f"{fname}();",
            "c": f"{fname}();",
            "cpp": f"{fname}();",
            "csharp": f"{fname}();",
            "java": f"{fname}();",
            "rust": f"{fname}();",
            "go": f"{fname}()",
            "kotlin": f"{fname}()",
            "swift": f"{fname}()",
            "quickbasic": f"CALL {fname}",
            "shell": f"{fname}",
            "lolcode": f"I IZ {fname} MKAY",
        }
        return rules.get(to_lang)

    if intent.kind == "list":
        var = intent.name
        items = intent.start.split(",") if intent.start else []
        if not items:
            return None

        def _lit(x: str) -> str:
            return x if re.fullmatch(r"-?\d+(?:\.\d+)?", x) else f'"{x}"'

        py_items = ", ".join(_lit(x) for x in items)
        sh_items = " ".join(_lit(x) for x in items)
        if to_lang == "python":
            return f"{var} = [{py_items}]"
        if to_lang == "javascript":
            return f"let {var} = [{py_items}];"
        if to_lang == "c":
            if all(re.fullmatch(r"-?\d+(?:\.\d+)?", x) for x in items):
                return f"int {var}[] = {{{py_items}}};"
            return f"const char *{var}[] = {{{py_items}}};"
        if to_lang == "cpp":
            return f"std::vector<{_cpp_elem_type(items)}> {var} = {{{py_items}}};"
        if to_lang == "csharp":
            return f"var {var} = new List<{_csharp_elem_type(items)}> {{ {py_items} }};"
        if to_lang == "java":
            return (
                f"java.util.List<{_java_elem_type(items)}> {var} = "
                f"java.util.List.of({py_items});"
            )
        if to_lang == "rust":
            return f"let {var} = vec![{py_items}];"
        if to_lang == "go":
            if all(re.fullmatch(r"-?\d+(?:\.\d+)?", x) for x in items):
                return f"{var} := []int{{{py_items}}}"
            return f"{var} := []string{{{py_items}}}"
        if to_lang == "kotlin":
            return f"val {var} = listOf({py_items})"
        if to_lang == "swift":
            return f"let {var} = [{py_items}]"
        if to_lang == "shell":
            return f"{var}=({sh_items})"
        if to_lang == "quickbasic":
            joined = ", ".join(items)
            return f"' list {var}: {joined}\nDIM {var}({len(items) - 1})"
        return None

    if intent.kind == "map":
        var = intent.name
        pairs = []
        for part in intent.start.split(";") if intent.start else []:
            if "=" not in part:
                continue
            k, v = part.split("=", 1)
            pairs.append((k, v))
        if not pairs:
            return None

        def _lit(x: str) -> str:
            return x if re.fullmatch(r"-?\d+(?:\.\d+)?", x) else f'"{x}"'

        if to_lang == "python":
            body = ", ".join(f"{_lit(k)}: {_lit(v)}" for k, v in pairs)
            return f"{var} = {{{body}}}"
        if to_lang == "javascript":
            body = ", ".join(f"{_lit(k)}: {_lit(v)}" for k, v in pairs)
            return f"let {var} = {{{body}}};"
        if to_lang == "c":
            keys = ", ".join(_lit(k) for k, _ in pairs)
            vals = ", ".join(_lit(v) for _, v in pairs)
            if all(re.fullmatch(r"-?\d+(?:\.\d+)?", v) for _, v in pairs):
                return (
                    f"const char *{var}_keys[] = {{{keys}}};\n"
                    f"int {var}_vals[] = {{{vals}}};"
                )
            return (
                f"const char *{var}_keys[] = {{{keys}}};\n"
                f"const char *{var}_vals[] = {{{vals}}};"
            )
        if to_lang == "cpp":
            body = ", ".join(f"{{{_lit(k)}, {_lit(v)}}}" for k, v in pairs)
            k_ty = "std::string" if not all(
                re.fullmatch(r"-?\d+(?:\.\d+)?", k) for k, _ in pairs
            ) else "int"
            v_ty = "int" if all(
                re.fullmatch(r"-?\d+(?:\.\d+)?", v) for _, v in pairs
            ) else "std::string"
            return f"std::map<{k_ty}, {v_ty}> {var} = {{{body}}};"
        if to_lang == "csharp":
            body = ", ".join(f"{{ {_lit(k)}, {_lit(v)} }}" for k, v in pairs)
            k_ty = "string" if not all(
                re.fullmatch(r"-?\d+(?:\.\d+)?", k) for k, _ in pairs
            ) else "int"
            v_ty = "int" if all(
                re.fullmatch(r"-?\d+(?:\.\d+)?", v) for _, v in pairs
            ) else "string"
            return f"var {var} = new Dictionary<{k_ty}, {v_ty}> {{ {body} }};"
        if to_lang == "java":
            puts = "; ".join(
                f"{var}.put({_lit(k)}, {_lit(v)})" for k, v in pairs
            )
            k_ty = "String" if not all(
                re.fullmatch(r"-?\d+(?:\.\d+)?", k) for k, _ in pairs
            ) else "Integer"
            v_ty = "Integer" if all(
                re.fullmatch(r"-?\d+(?:\.\d+)?", v) for _, v in pairs
            ) else "String"
            return (
                f"java.util.Map<{k_ty}, {v_ty}> {var} = new java.util.HashMap<>();\n"
                f"{puts};"
            )
        if to_lang == "rust":
            body = ", ".join(f"({_lit(k)}, {_lit(v)})" for k, v in pairs)
            return (
                f"let {var}: std::collections::HashMap<_, _> = "
                f"[{body}].into_iter().collect();"
            )
        if to_lang == "go":
            body = ", ".join(f"{_lit(k)}: {_lit(v)}" for k, v in pairs)
            k_ty = "string" if not all(
                re.fullmatch(r"-?\d+(?:\.\d+)?", k) for k, _ in pairs
            ) else "int"
            v_ty = "int" if all(
                re.fullmatch(r"-?\d+(?:\.\d+)?", v) for _, v in pairs
            ) else "string"
            return f"{var} := map[{k_ty}]{v_ty}{{{body}}}"
        if to_lang == "kotlin":
            body = ", ".join(f"{_lit(k)} to {_lit(v)}" for k, v in pairs)
            return f"val {var} = mapOf({body})"
        if to_lang == "swift":
            body = ", ".join(f"{_lit(k)}: {_lit(v)}" for k, v in pairs)
            return f"let {var} = [{body}]"
        if to_lang == "shell":
            # declare associative array when bash is available
            assigns = " ".join(f"[{_lit(k)}]={_lit(v)}" for k, v in pairs)
            return f"declare -A {var}=({assigns})"
        return None

    if intent.kind == "file":
        path = intent.name
        mode = intent.start
        if mode == "read":
            var = intent.end or "text"
            if to_lang == "python":
                return f'{var} = open("{path}").read()'
            if to_lang == "javascript":
                return (
                    f'const fs = require("fs");\n'
                    f'let {var} = fs.readFileSync("{path}", "utf8");'
                )
            if to_lang == "c":
                return (
                    f'char {var}[1024];\n'
                    f'FILE *f = fopen("{path}", "r");\n'
                    f"if (f) {{ fgets({var}, sizeof {var}, f); fclose(f); }}"
                )
            if to_lang == "cpp":
                return (
                    f"std::ifstream in(\"{path}\");\n"
                    f"std::string {var}((std::istreambuf_iterator<char>(in)),\n"
                    f"                    std::istreambuf_iterator<char>());"
                )
            if to_lang == "csharp":
                return f'string {var} = File.ReadAllText("{path}");'
            if to_lang == "java":
                return f'String {var} = java.nio.file.Files.readString(java.nio.file.Path.of("{path}"));'
            if to_lang == "rust":
                return f'let {var} = std::fs::read_to_string("{path}").unwrap();'
            if to_lang == "go":
                return (
                    f'{var}Bytes, _ := os.ReadFile("{path}")\n'
                    f'{var} := string({var}Bytes)'
                )
            if to_lang == "kotlin":
                return f'val {var} = java.io.File("{path}").readText()'
            if to_lang == "swift":
                return f'let {var} = try! String(contentsOfFile: "{path}")'
            if to_lang == "shell":
                return f'{var}=$(cat "{path}")'
            return None
        if mode == "write":
            content = intent.end or ""
            if to_lang == "python":
                return f'open("{path}", "w").write("{content}")'
            if to_lang == "javascript":
                return (
                    f'const fs = require("fs");\n'
                    f'fs.writeFileSync("{path}", "{content}");'
                )
            if to_lang == "c":
                return (
                    f'FILE *f = fopen("{path}", "w");\n'
                    f'if (f) {{ fputs("{content}", f); fclose(f); }}'
                )
            if to_lang == "cpp":
                return (
                    f'std::ofstream out("{path}");\n'
                    f'out << "{content}";'
                )
            if to_lang == "csharp":
                return f'File.WriteAllText("{path}", "{content}");'
            if to_lang == "java":
                return f'java.nio.file.Files.writeString(java.nio.file.Path.of("{path}"), "{content}");'
            if to_lang == "rust":
                return f'std::fs::write("{path}", "{content}").unwrap();'
            if to_lang == "go":
                return f'_ = os.WriteFile("{path}", []byte("{content}"), 0644)'
            if to_lang == "kotlin":
                return f'java.io.File("{path}").writeText("{content}")'
            if to_lang == "swift":
                return (
                    f'try! "{content}".write(toFile: "{path}", atomically: true, '
                    f'encoding: .utf8)'
                )
            if to_lang == "shell":
                return f'printf "%s" "{content}" > "{path}"'
            return None
        return None

    return None


def _c_assignment(var: str, val: str) -> str:
    """Pick a simple C type for an assignment teaching fragment."""
    if re.fullmatch(r"'[^']*'|\"[^\"]*\"", val):
        return f"char *{var} = {val};"
    return f"int {var} = {val};"


def _cpp_assignment(var: str, val: str) -> str:
    """Pick a simple C++ type for an assignment teaching fragment."""
    if re.fullmatch(r"'[^']*'|\"[^\"]*\"", val):
        return f"std::string {var} = {val};"
    return f"int {var} = {val};"


def _cpp_elem_type(items: list[str]) -> str:
    if all(re.fullmatch(r"-?\d+(?:\.\d+)?", x) for x in items):
        return "int"
    return "std::string"


def _csharp_assignment(var: str, val: str) -> str:
    """Pick a simple C# type for an assignment teaching fragment."""
    if re.fullmatch(r"'[^']*'|\"[^\"]*\"", val):
        return f"string {var} = {val};"
    return f"int {var} = {val};"


def _csharp_elem_type(items: list[str]) -> str:
    if all(re.fullmatch(r"-?\d+(?:\.\d+)?", x) for x in items):
        return "int"
    return "string"


def _java_assignment(var: str, val: str) -> str:
    """Pick a simple Java type for an assignment teaching fragment."""
    if re.fullmatch(r"'[^']*'|\"[^\"]*\"", val):
        return f"String {var} = {val};"
    return f"int {var} = {val};"


def _java_elem_type(items: list[str]) -> str:
    if all(re.fullmatch(r"-?\d+(?:\.\d+)?", x) for x in items):
        return "Integer"
    return "String"


def _rust_assignment(var: str, val: str) -> str:
    """Pick a simple Rust binding for an assignment teaching fragment."""
    if re.fullmatch(r"'[^']*'|\"[^\"]*\"", val):
        return f"let {var} = {val};"
    return f"let {var} = {val};"


def _go_assignment(var: str, val: str) -> str:
    """Pick a simple Go short declaration for an assignment teaching fragment."""
    return f"{var} := {val}"


def _kotlin_assignment(var: str, val: str) -> str:
    """Pick a simple Kotlin binding for an assignment teaching fragment."""
    return f"val {var} = {val}"


def _swift_assignment(var: str, val: str) -> str:
    """Pick a simple Swift binding for an assignment teaching fragment."""
    return f"var {var} = {val}"
