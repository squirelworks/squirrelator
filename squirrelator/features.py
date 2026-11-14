"""Feature switches and Settings levels from squirrel-lang-data's features.json.

Same ids, labels and Simple / More / Everything rules as LanguageStudentDesk
(#201). The file is read from the data checkout; this module never invents
switches. A level turns on every feature whose level is at or below it.
Changing one switch in Customize shows "Custom".

    load()                  the features.json object
    Settings()              remembered level and Customize switches
    settings.is_on(id)      is a switch on?
    settings.allows(item)   may this content show? (its "requires")
"""

from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .data import data_dir

SCHEMA = "features@1"
CUSTOM = "custom"
SETTINGS_NAME = "settings.json"
TEXT_KEYS = ("notice", "welcomeTitle", "welcomeBody", "whatsInApp", "customize", "custom")

# Programming languages the rules engine already groups, tagged with the
# matching feature id from features.json (not invented here).
LANGUAGE_REQUIRES = {
    "quickbasic": "programming-older",
    "z80": "programming-older",
    "brainfood": "programming-joke",
    "lolcode": "programming-joke",
}


@dataclass(frozen=True)
class Level:
    id: str
    label: str
    description: str


@dataclass(frozen=True)
class Feature:
    id: str
    label: str
    description: str
    level: str
    added: str


@dataclass(frozen=True)
class FeaturesData:
    """The switches and levels from features.json, plus shared UI strings."""

    levels: tuple[Level, ...]
    features: tuple[Feature, ...]
    default_level: str
    featured: tuple[str, ...]
    text: dict[str, str]
    schema: str = SCHEMA

    @property
    def level_ids(self) -> tuple[str, ...]:
        return tuple(lv.id for lv in self.levels)

    def feature(self, fid: str) -> Feature | None:
        return next((f for f in self.features if f.id == fid), None)


def _blank_text() -> dict[str, str]:
    return {k: "" for k in TEXT_KEYS}


def _empty() -> FeaturesData:
    return FeaturesData((), (), "simple", (), _blank_text())


def _parse(raw: dict[str, Any]) -> FeaturesData:
    levels = tuple(
        Level(lv["id"], lv["label"], lv["description"]) for lv in raw.get("levels") or []
        if isinstance(lv, dict) and {"id", "label", "description"} <= lv.keys()
    )
    level_ids = {lv.id for lv in levels}
    features = tuple(
        Feature(f["id"], f["label"], f["description"], f["level"], f["added"])
        for f in raw.get("features") or []
        if isinstance(f, dict)
        and {"id", "label", "description", "level", "added"} <= f.keys()
        and f["level"] in level_ids
    )
    default = raw.get("defaultLevel") or (levels[0].id if levels else "simple")
    if default not in level_ids and levels:
        default = levels[0].id
    featured = tuple(x for x in (raw.get("featured") or []) if isinstance(x, str))
    text = _blank_text()
    for k, v in (raw.get("text") or {}).items():
        if isinstance(v, str) and v.strip():
            text[k] = v
    return FeaturesData(levels, features, default, featured, text, raw.get("schema", SCHEMA))


def load(path: str | os.PathLike | None = None) -> FeaturesData:
    """Read features.json from the data checkout (or an explicit path)."""
    try:
        root = Path(path) if path is not None else data_dir()
        raw = json.loads((root / "features.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return _empty()
    if not isinstance(raw, dict) or raw.get("schema") != SCHEMA:
        return _empty()
    return _parse(raw)


def settings_path() -> Path:
    """Where squirrelator remembers Settings between sessions."""
    if sys.platform == "win32":
        root = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return root / "squirrelator" / SETTINGS_NAME


def _rank(data: FeaturesData, level: str) -> int:
    try:
        return data.level_ids.index(level)
    except ValueError:
        return 0


def on_at_level(data: FeaturesData, feature: Feature, level: str) -> bool:
    """On at this level: the feature's level is at or below it."""
    return _rank(data, feature.level) <= _rank(data, level)


@dataclass
class Settings:
    """Remembered Show level and Customize switches for one session (or disk)."""

    data: FeaturesData = field(default_factory=load)
    level: str = ""
    switches: dict[str, bool] = field(default_factory=dict)
    notice_dismissed: bool = False
    welcome_done: bool = False
    _listeners: list[Callable[["Settings"], None]] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        if not self.level:
            self.level = self.data.default_level or (self.data.level_ids[0] if self.data.level_ids else "simple")
        self.level, self.switches = self._clean_level(self.level, self.switches)

    def _clean_level(self, level: str, switches: dict[str, bool]) -> tuple[str, dict[str, bool]]:
        ids = {f.id for f in self.data.features}
        cleaned = {k: bool(v) for k, v in switches.items() if k in ids and isinstance(v, bool)}
        if level == CUSTOM or level in self.data.level_ids:
            return level, cleaned if level == CUSTOM else {}
        return self.data.default_level or "simple", {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "switches": dict(self.switches) if self.level == CUSTOM else {},
            "noticeDismissed": self.notice_dismissed,
            "welcomeDone": self.welcome_done,
        }

    @classmethod
    def from_dict(cls, raw: Any, data: FeaturesData | None = None) -> Settings:
        data = data or load()
        out = cls(data=data)
        if isinstance(raw, dict):
            out.level, out.switches = out._clean_level(
                raw.get("level") or out.level,
                raw.get("switches") if isinstance(raw.get("switches"), dict) else {},
            )
            out.notice_dismissed = bool(raw.get("noticeDismissed"))
            out.welcome_done = bool(raw.get("welcomeDone"))
        return out

    def on_change(self, fn: Callable[[Settings], None]) -> None:
        self._listeners.append(fn)

    def _notify(self) -> None:
        for fn in list(self._listeners):
            fn(self)

    def is_on(self, fid: str) -> bool:
        f = self.data.feature(fid)
        if not f:
            return False
        if self.level == CUSTOM:
            return self.switches.get(fid) is True
        return on_at_level(self.data, f, self.level)

    def allows(self, item: Any) -> bool:
        """Content tags the features it needs with requires (one id or a list)."""
        req = item.get("requires") if isinstance(item, dict) else getattr(item, "requires", None)
        if not req:
            return True
        needed = req if isinstance(req, (list, tuple)) else [req]
        return all(self.is_on(r) for r in needed)

    def allows_language(self, lang: str) -> bool:
        req = LANGUAGE_REQUIRES.get(lang)
        return self.allows({"requires": req} if req else {})

    def set_level(self, level: str) -> None:
        if level not in self.data.level_ids:
            return
        self.level = level
        self.switches = {}
        self._notify()

    def set(self, fid: str, on: bool) -> None:
        """One switch changed: keep the others, match a level or show Custom."""
        now = {f.id: self.is_on(f.id) for f in self.data.features}
        now[fid] = bool(on)
        match = next(
            (lv for lv in self.data.level_ids
             if all(now[f.id] == on_at_level(self.data, f, lv) for f in self.data.features)),
            None,
        )
        if match:
            self.level = match
            self.switches = {}
        else:
            self.level = CUSTOM
            self.switches = now
        self._notify()

    def customize_order(self) -> list[Feature]:
        """Newest first, then by label, so a new switch shows at the top."""
        return sorted(self.data.features, key=lambda f: (-_date_key(f.added), f.label))

    def save(self, path: Path | None = None) -> None:
        dest = path or settings_path()
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")
        except OSError:
            pass

    @classmethod
    def load_saved(cls, path: Path | None = None, data: FeaturesData | None = None) -> Settings:
        data = data or load()
        src = path or settings_path()
        try:
            return cls.from_dict(json.loads(src.read_text(encoding="utf-8")), data)
        except (OSError, ValueError):
            return cls(data=data)


def _date_key(added: str) -> int:
    try:
        y, m, d = added.split("-")
        return int(y) * 10000 + int(m) * 100 + int(d)
    except (ValueError, AttributeError):
        return 0


def snapshot(settings: Settings) -> Settings:
    """A disconnected copy (for tests that mutate without touching disk)."""
    return Settings.from_dict(deepcopy(settings.to_dict()), settings.data)
