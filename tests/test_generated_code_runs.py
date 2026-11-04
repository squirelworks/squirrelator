"""Run the code that English → code produces today, in every target CI can
run, and check what it prints. Targets whose interpreter is missing locally
are skipped; CI has Python, Node and bash."""

import shutil
import sqlite3
import subprocess
import sys

import pytest

from squirrelator import translate

# English input → what the generated program prints (one value per line).
PROGRAMS = [
    ("print hello", ["hello"]),
    ("show 'Good morning'", ["good morning"]),
    ("count from 1 to 5", ["1", "2", "3", "4", "5"]),
    ("loop 3 through 7", ["3", "4", "5", "6", "7"]),
    ("set total to 42", []),
]

RUNNERS = {
    "python": [sys.executable, "-c"],
    "javascript": ["node", "-e"],
    "shell": ["bash", "-c"],
}


@pytest.mark.parametrize("target", sorted(RUNNERS))
@pytest.mark.parametrize("source, printed", PROGRAMS)
def test_generated_program_runs(target, source, printed):
    cmd = RUNNERS[target]
    if shutil.which(cmd[0]) is None:
        pytest.skip(f"{cmd[0]} not installed")
    code = translate(source, "english", target)
    r = subprocess.run([*cmd, code], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == printed


def test_generated_sql_runs():
    code = translate("print hello", "english", "sql")
    rows = sqlite3.connect(":memory:").execute(code).fetchall()
    assert rows == [("hello",)]
