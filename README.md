# squirrelator

Core language engine for translating between human languages, programming languages, and pseudocode.

**squirrelator** holds the shared language logic.  
**LanguageStudentDesk** consumes it to provide learning tools.

## Run (GUI is default)

```bash
cd ~/FU/squirrelator
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

- English / pseudocode → Python, JavaScript, QuickBASIC, LOLCODE, brainFOOD, Z80, Shell, SQL
- Code → English explanations
- Simple code ↔ code via intermediate English

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Using from LanguageStudentDesk

```python
from squirrelator import translate
result = translate("print hello", from_lang="english", to_lang="python")
```

## Supported languages

english, pseudocode, python, javascript, quickbasic, brainfood, lolcode, z80, shell, sql
