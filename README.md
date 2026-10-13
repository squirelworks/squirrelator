# squirrelator

Core language engine for translating between human languages, programming languages, and pseudocode.

**squirrelator** holds the shared language logic.  
**LanguageStudentDesk** consumes it to provide learning tools.

## Purpose

Take text in one form and produce it in another:

- Human language → programming language
- Programming language → programming language
- Programming language → human language
- Pseudocode ↔ any of the above

## Layout

```
squirrelator/
├── squirrelator/          # Python package (importable core)
│   ├── __init__.py
│   ├── translator.py   # main translation interface
│   ├── languages/      # language definitions / mappings
│   └── examples.py     # built-in sample translations
├── app/                  # simple web UI (optional)
│   └── index.html
├── tests/
│   └── test_translator.py
└── pyproject.toml
```

## Quick start

```bash
git clone https://github.com/squirelworks/squirrelator
cd squirrelator
pip install -e .
python -c "from squirrelator import translate; print(translate('print hello', 'pseudocode', 'python'))"
```

## Using from LanguageStudentDesk

```python
# in LSDesk or any consumer
from squirrelator import translate

result = translate(
    source="for each number from 1 to 5, print it",
    from_lang="english",
    to_lang="python"
)
```

The web app under `app/` is a lightweight demo. The real value is the importable package.
