"""The bridge the native apps (native/) call, and the language data they ship.

The Kotlin side is tested by Gradle; this checks the Python half with the
real engine.
"""

import io
import json
import shutil
import sys
from pathlib import Path

import pytest

from squirrelator import data, translate
from squirrelator.menus import RULES, languages_for

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "native" / "python"))
import squirrelator_bridge as bridge  # noqa: E402

try:
    data.data_dir()
except data.DataNotFound:
    pytest.skip("squirrel-lang-data not checked out", allow_module_level=True)

# What native/android/build.gradle.kts packs into the app (packLangData).
SHIPPED = ("features.json", "LICENSE", "languages", "meaning")


def test_languages_cover_both_engines_in_menu_order():
    from squirrelator.pipeline import languages

    langs = bridge.languages()
    assert len(langs) == len(set(langs))
    assert set(languages_for(RULES)) <= set(langs)
    # translate() defaults to engine="auto", which reaches the pipeline too.
    assert set(languages()) <= set(langs)
    # Human languages A to Z, then pseudocode and code in the rules order.
    split = langs.index("pseudocode")
    assert langs[:split] == sorted(langs[:split])
    rules = languages_for(RULES)
    assert langs[split:] == rules[rules.index("pseudocode"):]


def test_a_pipeline_pair_goes_through_with_the_defaults():
    assert bridge.translate("バスで学校に行きます。", "japanese", "english") == "I go to school by bus."


def test_translate_is_the_engines_translate_with_defaults():
    assert bridge.translate("print hello", "english", "python") == translate("print hello", "english", "python")


def test_show_is_what_the_desktop_gui_shows_under_auto():
    from squirrelator.menus import AUTO, PIPELINE, display

    assert bridge.show("print hello", "english", "python") == ['print("hello")', RULES]
    text, used = bridge.show("バスで学校に行きます。", "japanese", "english")
    assert used == PIPELINE and text.startswith("I go to school by bus.") and "Alpha." in text
    shown = bridge.show("I drink water.", "english", "latin")
    assert shown == list(display("I drink water.", "english", "latin", AUTO))
    assert "Second opinion from Pipeline (alpha)" in shown[0] and "Aquam bibō." in shown[0]


def test_serve_answers_one_json_line_per_request():
    requests = [
        {"op": "languages"},
        {"op": "translate", "text": "print hello", "from": "english", "to": "python"},
        {"op": "show", "text": "print hello", "from": "english", "to": "python"},
        {"op": "nope"},
        {"op": "translate"},
    ]
    out = io.StringIO()
    bridge.serve(io.StringIO("\n".join(json.dumps(r) for r in requests) + "\n\n"), out)
    replies = [json.loads(line) for line in out.getvalue().splitlines()]
    assert replies[0] == {"ok": True, "languages": bridge.languages()}
    assert replies[1] == {"ok": True, "text": 'print("hello")'}
    assert replies[2] == {"ok": True, "text": 'print("hello")', "engine": RULES, "mode": "Auto"}
    assert replies[3]["ok"] is False and "nope" in replies[3]["error"]
    assert replies[4]["ok"] is False and "KeyError" in replies[4]["error"]


def test_setup_points_the_engine_at_the_apps_data(tmp_path, monkeypatch):
    # Set first so monkeypatch puts the old value back after the test.
    monkeypatch.setenv(data.ENV_VAR, "placeholder")
    bridge.setup(str(tmp_path))
    assert data.os.environ[data.ENV_VAR] == str(tmp_path)


def test_the_shipped_data_is_all_the_engine_needs(tmp_path, monkeypatch, root):
    """The app carries only part of squirrel-lang-data. The engine must give
    the same answers from that part as from the whole checkout."""
    from squirrelator.pipeline import languages, run

    for name in SHIPPED:
        src = root / name
        (shutil.copytree if src.is_dir() else shutil.copy)(src, tmp_path / name)
    full_langs = languages(root=root)
    full = run("バスで学校に行きます。", "japanese", "english", root=root)

    monkeypatch.setenv(data.ENV_VAR, str(tmp_path))
    assert languages(root=tmp_path) == full_langs
    assert run("バスで学校に行きます。", "japanese", "english", root=tmp_path) == full
    assert bridge.translate("print hello", "english", "python") == 'print("hello")'
