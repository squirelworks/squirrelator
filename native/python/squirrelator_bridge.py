"""The small piece of Python the native apps talk to.

The screens are Kotlin; the translation engine stays the one Python package
in squirrelator/. This module is the only thing they call:

- Android loads it in-process through Chaquopy (native/android).
- Desktop runs ``python3 squirrelator_bridge.py --serve`` and talks to it one
  JSON line at a time over stdin and stdout (native/desktop).

It only wraps the engine's public API and adds no translation logic.
"""

import inspect
import json
import os
import sys

from squirrelator import translate as _translate
from squirrelator.data import ENV_VAR
from squirrelator.menus import RULES, languages_for


def setup(data_path: str) -> None:
    """Point the engine at the squirrel-lang-data copy shipped with the app."""
    os.environ[ENV_VAR] = data_path


def _default_engine() -> str:
    return inspect.signature(_translate).parameters["engine"].default


def languages() -> list[str]:
    """The languages translate() can handle with its default settings.

    The rules engine's languages, plus the data-driven pipeline's when the
    default engine can reach it. Menu order, as AGENTS.md asks: human
    languages A to Z, then pseudocode and programming languages in the
    rules engine's order.
    """
    rules = languages_for(RULES)
    split = rules.index("pseudocode") if "pseudocode" in rules else len(rules)
    human, code = rules[:split], rules[split:]
    if _default_engine() != "rules":
        from squirrelator.pipeline import languages as pipeline_languages

        try:
            human = sorted(set(human) | set(pipeline_languages()))
        except Exception:
            pass
    return human + code


def translate(text: str, from_lang: str, to_lang: str) -> str:
    """translate() with its defaults, the same call LanguageStudentDesk makes."""
    return _translate(text, from_lang, to_lang)


def _handle(request: dict) -> dict:
    op = request.get("op")
    if op == "languages":
        return {"ok": True, "languages": languages()}
    if op == "translate":
        return {"ok": True, "text": translate(request["text"], request["from"], request["to"])}
    return {"ok": False, "error": f"unknown op {op!r}"}


def serve(stdin=sys.stdin, stdout=sys.stdout) -> None:
    """Answer one JSON request per line until stdin closes."""
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            reply = _handle(json.loads(line))
        except Exception as e:  # report it to the app instead of dying
            reply = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
        stdout.flush()


if __name__ == "__main__":
    if "--serve" in sys.argv:
        serve()
    else:
        print("Usage: python3 squirrelator_bridge.py --serve", file=sys.stderr)
        sys.exit(2)
