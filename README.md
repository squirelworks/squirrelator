# squirrelator

Core language engine for translating between human languages, programming languages, and pseudocode.

**squirrelator** holds the shared language logic.  
**LanguageStudentDesk** consumes it to provide learning tools.

## What it does

Rule-based translation for common patterns:

- English / pseudocode → Python, JavaScript, QuickBASIC, LOLCODE, brainFOOD, Z80, Shell, SQL
- Code → English explanations
- Simple code ↔ code via intermediate English

## Quick start

```bash
git clone https://github.com/squirelworks/squirrelator
cd squirrelator
pip install -e .

python -c "from squirrelator import translate; print(translate('print hello', 'english', 'python'))"
python -c "from squirrelator import translate; print(translate('FOR i = 1 TO 5\\n  PRINT i\\nNEXT i', 'quickbasic', 'english'))"
```

## Web app

Open `app/index.html` in a browser. It contains a self-contained JavaScript version of the translator so it works without a server.

## Using from LanguageStudentDesk

```python
from squirrelator import translate
result = translate("print hello", from_lang="english", to_lang="python")
```

## Supported languages

english, pseudocode, python, javascript, quickbasic, brainfood, lolcode, z80, shell, sql
