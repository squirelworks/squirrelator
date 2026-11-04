import pytest

from squirrelator import data
from squirrelator.data import ENV_VAR, DataNotFound, data_dir


def fake_checkout(path):
    path.mkdir(parents=True, exist_ok=True)
    (path / data.MARKER).write_text("{}", encoding="utf-8")
    return path


def test_explicit_path_wins(tmp_path, monkeypatch):
    monkeypatch.setenv(ENV_VAR, str(fake_checkout(tmp_path / "env")))
    given = fake_checkout(tmp_path / "given")
    assert data_dir(given) == given


def test_env_var_beats_submodule(tmp_path, monkeypatch):
    env = fake_checkout(tmp_path / "env")
    monkeypatch.setenv(ENV_VAR, str(env))
    monkeypatch.setattr(data, "SUBMODULE", fake_checkout(tmp_path / "sub"))
    assert data_dir() == env


def test_falls_back_to_submodule(tmp_path, monkeypatch):
    monkeypatch.delenv(ENV_VAR, raising=False)
    sub = fake_checkout(tmp_path / "sub")
    monkeypatch.setattr(data, "SUBMODULE", sub)
    assert data_dir() == sub


def test_bad_env_var_is_an_error_not_a_silent_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv(ENV_VAR, str(tmp_path / "missing"))
    monkeypatch.setattr(data, "SUBMODULE", fake_checkout(tmp_path / "sub"))
    with pytest.raises(DataNotFound, match=ENV_VAR):
        data_dir()


def test_nothing_found(tmp_path, monkeypatch):
    monkeypatch.delenv(ENV_VAR, raising=False)
    monkeypatch.setattr(data, "SUBMODULE", tmp_path / "empty")
    with pytest.raises(DataNotFound, match="submodule update"):
        data_dir()


def test_pinned_submodule_is_checked_out(monkeypatch):
    """CI checks out submodules, so the pinned data must be found there."""
    monkeypatch.delenv(ENV_VAR, raising=False)
    if not (data.SUBMODULE / ".git").exists():
        pytest.skip("data/ submodule not initialized")
    assert data_dir() == data.SUBMODULE
