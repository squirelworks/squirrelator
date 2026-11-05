# squirrelator

Core language engine for translating between human languages, programming languages, and pseudocode.

**squirrelator** holds the shared language logic.  
**LanguageStudentDesk** consumes it to provide learning tools.

## Run (GUI is default)

```bash
cd squirrelator
source .venv/bin/activate
python3 squirrelator.py
```

Or:

```bash
python3 -m squirrelator
```

### CLI only if you ask for it

```bash
python3 squirrelator.py --cli english python "print hello"
python3 -m squirrelator --cli quickbasic english 'PRINT "Hi"'
```

## Web demo

Open `app/index.html` in a browser (self-contained, no install needed).

## What it does

Rule-based translation for common patterns:

- English or pseudocode → code in a programming language
- Code → plain-English explanations
- Simple code ↔ code, through an English intermediate

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
git submodule update --init   # the language data, at data/
```

The language data comes from
[squirrel-lang-data](https://github.com/squirelworks/squirrel-lang-data),
pinned as a submodule at `data/`. To use another checkout instead (LSD hands
squirrelator its own), set `SQUIRREL_LANG_DATA` to its path.

## Using from LanguageStudentDesk

```python
from squirrelator import translate
result = translate("print hello", from_lang="english", to_lang="python")
```

`translate()` returns the translated text. `translate_full()` takes the same
arguments and returns a `Translation` with the text, its alternatives, a
step-by-step breakdown, the parts of the source it didn't understand, a
confidence and an alpha flag. It raises `UnsupportedLanguage` for a language
it doesn't know.

Both take an `engine`. The default, `engine="auto"`, uses the data-driven
pipeline (alpha) for sentences between English, Latin and Klingon, the
rule-based engine for code and every other pair it supports, and the
pipeline for a pair the rules don't support but the pipeline does. The pipeline reads every word from squirrel-lang-data and
marks what the data doesn't cover instead of guessing:

```python
translate("バスで学校に行きます。", "japanese", "english")
# 'I go to school by bus.'
```

Pass `engine="rules"` or `engine="pipeline"` to choose one. Between
English, Latin and Klingon, `auto` keeps the rules result for a code
instruction the rules understand at least as well ("print hello"), and
`translate_full()` gives the other engine's answer as `second_opinion`.
The pipeline declines and conjugates Latin and gives Klingon verbs their
prefixes and suffixes from the data's inflection tables. Without the
language data, `auto` is the rules engine. `squirrelator.pipeline.languages()` lists the
languages the pipeline can read.

## Supported languages

The **From** and **To** menus in the GUI and the web app list every language
squirrelator can translate today. Calling `translate()` with a language it
doesn't know returns the current list.
