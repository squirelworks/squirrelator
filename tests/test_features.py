"""features.json Settings: same ids/labels and level rules as LSD (#201)."""

import json

import pytest

from squirrelator import data
from squirrelator.features import CUSTOM, LANGUAGE_REQUIRES, Settings, load
from squirrelator.menus import AUTO, RULES, languages_for


def test_load_reads_features_json_from_data():
    try:
        data.data_dir()
    except data.DataNotFound:
        pytest.skip("squirrel-lang-data not checked out")
    raw = json.loads((data.data_dir() / "features.json").read_text(encoding="utf-8"))
    got = load()
    assert got.schema == "features@1"
    assert [lv.id for lv in got.levels] == [lv["id"] for lv in raw["levels"]]
    assert [f.id for f in got.features] == [f["id"] for f in raw["features"]]
    assert got.default_level == raw["defaultLevel"]
    assert got.featured == tuple(raw["featured"])
    for key in ("notice", "customize", "custom", "whatsInApp"):
        assert got.text[key] == raw["text"][key]
    # Labels come from data, not from hardcoded English in this package.
    by_id = {f.id: f for f in got.features}
    assert by_id["historical"].label == "Historical stages"
    assert by_id["programming-joke"].level == "simple"


def test_simple_turns_on_simple_features_only():
    try:
        data.data_dir()
    except data.DataNotFound:
        pytest.skip("squirrel-lang-data not checked out")
    s = Settings(data=load())
    assert s.level == "simple"
    assert s.is_on("alpha") and s.is_on("programming-joke") and s.is_on("programming-older")
    assert not s.is_on("regional") and not s.is_on("historical")
    s.set_level("more")
    assert s.is_on("regional") and s.is_on("pronunciation") and s.is_on("character-forms")
    assert not s.is_on("historical")
    s.set_level("everything")
    assert s.is_on("historical")


def test_customize_shows_custom_then_snaps_back_to_a_level():
    try:
        data.data_dir()
    except data.DataNotFound:
        pytest.skip("squirrel-lang-data not checked out")
    s = Settings(data=load())
    s.set("historical", True)
    assert s.level == CUSTOM
    assert s.is_on("historical") and s.is_on("alpha")
    # Turning historical off while still on Simple's set of switches snaps back.
    s.set("historical", False)
    assert s.level == "simple"
    assert s.switches == {}


def test_settings_round_trip_on_disk(tmp_path):
    try:
        data.data_dir()
    except data.DataNotFound:
        pytest.skip("squirrel-lang-data not checked out")
    path = tmp_path / "settings.json"
    s = Settings(data=load())
    s.set("regional", True)
    s.notice_dismissed = True
    s.save(path)
    loaded = Settings.load_saved(path)
    assert loaded.level == CUSTOM
    assert loaded.is_on("regional") and not loaded.is_on("historical")
    assert loaded.notice_dismissed


def test_allows_and_language_requires():
    try:
        data.data_dir()
    except data.DataNotFound:
        pytest.skip("squirrel-lang-data not checked out")
    s = Settings(data=load())
    assert LANGUAGE_REQUIRES["brainfood"] == "programming-joke"
    assert s.allows_language("python") and s.allows_language("brainfood")
    s.set("programming-joke", False)
    assert s.level == CUSTOM
    assert not s.allows_language("brainfood") and not s.allows_language("lolcode")
    assert s.allows_language("python") and s.allows_language("quickbasic")
    assert not s.allows({"requires": "programming-joke"})
    assert s.allows({"requires": ["programming-older"]})


def test_menus_hide_languages_when_their_switch_is_off():
    try:
        data.data_dir()
    except data.DataNotFound:
        pytest.skip("squirrel-lang-data not checked out")
    s = Settings(data=load())
    assert "brainfood" in languages_for(RULES, s)
    s.set("programming-joke", False)
    s.set("programming-older", False)
    rules = languages_for(RULES, s)
    auto = languages_for(AUTO, s)
    for lang in ("brainfood", "lolcode", "quickbasic", "z80"):
        assert lang not in rules and lang not in auto
    assert "python" in rules and "english" in auto


def test_app_features_js_matches_data():
    """The web twin's generated copy must stay in sync with features.json."""
    try:
        data.data_dir()
    except data.DataNotFound:
        pytest.skip("squirrel-lang-data not checked out")
    from pathlib import Path
    import subprocess
    repo = Path(__file__).resolve().parents[1]
    gen = repo / "data" / "tools" / "gen_features.py"
    out = repo / "app" / "features.js"
    r = subprocess.run(["python3", str(gen), str(out), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_missing_data_yields_empty_features(tmp_path, monkeypatch):
    monkeypatch.delenv(data.ENV_VAR, raising=False)
    monkeypatch.setattr(data, "SUBMODULE", tmp_path / "empty")
    got = load()
    assert got.features == () and got.levels == ()
    s = Settings(data=got)
    assert not s.is_on("alpha")
