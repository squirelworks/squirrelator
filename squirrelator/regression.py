"""Golden and optional pair regression report (ROADMAP Phase 5).

Golden cases are always `tests/golden/translations.json` via default
translate(). Pair accept lists, when present, live in the pinned
squirrel-lang-data checkout under `testing/translation-pairs/` (same
`translation-pair-tests/1` shape as LanguageStudentDesk's TL tests). Source
text is rendered from the meaning-matrix column at measure time. Until that
data folder ships, the report is golden-only — no checkout of
LanguageStudentDesk, and no hard failure when pairs are absent.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import translate
from .coverage import _column_text
from .data import DataNotFound, data_dir
from .matrix import matrix
from .pipeline import run

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = ROOT / "tests" / "golden" / "translations.json"
PAIR_SUBDIR = Path("testing") / "translation-pairs"


@dataclass(frozen=True)
class PairCaseResult:
    language: str
    sentence: str
    source: str
    got: str
    ok: bool


@dataclass(frozen=True)
class PairSuite:
    language: str
    total: int
    passed: int
    misses: tuple[PairCaseResult, ...]

    @property
    def rate(self) -> float:
        return self.passed / self.total if self.total else 0.0


@dataclass(frozen=True)
class GoldenSuite:
    total: int
    passed: int
    misses: tuple[tuple[str, str, str, str, str], ...]

    @property
    def rate(self) -> float:
        return self.passed / self.total if self.total else 0.0


@dataclass(frozen=True)
class RegressionReport:
    pairs: tuple[PairSuite, ...]
    golden: GoldenSuite
    data_pin: str = ""
    pair_tests: str = ""


def _data_pin() -> str:
    import subprocess
    try:
        root = data_dir()
        tag = subprocess.run(
            ["git", "-C", str(root), "describe", "--tags", "--exact-match"],
            capture_output=True, text=True, check=False,
        ).stdout.strip()
        if tag:
            return tag
        return subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=False,
        ).stdout.strip()
    except Exception:
        return ""


def pair_tests_dir(root=None) -> Path | None:
    """Pinned data's testing/translation-pairs/, or None when absent."""
    try:
        base = Path(root) if root is not None else data_dir()
    except DataNotFound:
        return None
    path = base / PAIR_SUBDIR
    return path if path.is_dir() else None


def load_pair_fixtures(directory: Path | None = None) -> list[dict]:
    directory = directory if directory is not None else pair_tests_dir()
    if directory is None or not directory.is_dir():
        return []
    out = []
    for path in sorted(directory.glob("*-english.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema") != "translation-pair-tests/1":
            continue
        if data.get("into") != "english":
            continue
        out.append(data)
    return out


def measure_pairs(directory: Path | None = None, *, root=None) -> tuple[PairSuite, ...]:
    mx = matrix(root)
    suites: list[PairSuite] = []
    for fixture in load_pair_fixtures(directory):
        lang = fixture["language"]
        cols = mx.columns.get(lang, {})
        misses: list[PairCaseResult] = []
        passed = 0
        total = 0
        for case in fixture.get("cases") or []:
            sid = case.get("sentence")
            expect = list(case.get("accept") or [])
            if not sid or not expect:
                continue
            rendering = cols.get(sid)
            if rendering is None:
                continue
            total += 1
            source = _column_text(rendering)
            got = run(source, lang, "english", root=root).text
            ok = got in set(expect)
            if ok:
                passed += 1
            else:
                misses.append(PairCaseResult(lang, sid, source, got, False))
        if total:
            suites.append(PairSuite(lang, total, passed, tuple(misses)))
    return tuple(suites)


def measure_golden(path: Path | None = None) -> GoldenSuite:
    path = path or GOLDEN_PATH
    cases = json.loads(path.read_text(encoding="utf-8"))
    misses: list[tuple[str, str, str, str, str]] = []
    passed = 0
    for case in cases:
        frm, to = case["from"].strip(), case["to"].strip()
        source, expected = case["source"], case["expected"]
        got = translate(source, frm, to)
        if got == expected:
            passed += 1
        else:
            misses.append((frm, to, source, got, expected))
    return GoldenSuite(len(cases), passed, tuple(misses))


def measure(directory: Path | None = None, *, root=None) -> RegressionReport:
    pairs_dir = directory if directory is not None else pair_tests_dir(root)
    return RegressionReport(
        pairs=measure_pairs(directory, root=root),
        golden=measure_golden(),
        data_pin=_data_pin(),
        pair_tests=str(pairs_dir) if pairs_dir else "",
    )


def write_report(path: str | Path, directory: Path | None = None, *, root=None) -> RegressionReport:
    report = measure(directory, root=root)
    path = Path(path)
    lines = [
        "# squirrelator regression report",
        "",
        "Generated by `squirrelator.regression` (ROADMAP Phase 5).",
        "Golden cases are `tests/golden/translations.json`. Pair accept lists,",
        "when present, are read from the pinned data under",
        "`testing/translation-pairs/`; source text is rendered from the",
        "meaning-matrix column at measure time.",
        "",
    ]
    if report.data_pin:
        lines += [f"Data pin: `{report.data_pin}`.", ""]
    if report.pair_tests:
        lines += [f"Pair tests: `{report.pair_tests}`.", ""]
    else:
        lines += [
            "Pair tests: none in this data pin yet "
            "(`testing/translation-pairs/`).",
            "",
        ]

    lines += [
        "## Golden translations (default translate)",
        "",
        f"{report.golden.passed}/{report.golden.total} cases still match"
        f" ({report.golden.rate:.0%}).",
        "",
    ]
    if report.golden.misses:
        lines.append("Misses (from → to):")
        for frm, to, source, got, expected in report.golden.misses[:40]:
            lines.append(f"- `{frm}` → `{to}`: {source!r} → {got!r} (expected {expected!r})")
        if len(report.golden.misses) > 40:
            lines.append(f"- …and {len(report.golden.misses) - 40} more")
        lines.append("")

    lines += [
        "## Pipeline pair fixtures (column → English)",
        "",
    ]
    if not report.pairs:
        lines += ["No pair fixtures in this data pin.", ""]
    else:
        lines += [
            "| Language | Pass | Total | Rate |",
            "|---|---:|---:|---:|",
        ]
        for suite in report.pairs:
            lines.append(
                f"| {suite.language} | {suite.passed} | {suite.total} | {suite.rate:.0%} |"
            )
        total_pass = sum(s.passed for s in report.pairs)
        total_n = sum(s.total for s in report.pairs)
        lines += [
            "",
            f"All pairs: {total_pass}/{total_n}"
            + (f" ({total_pass / total_n:.0%})." if total_n else "."),
            "",
        ]
        misses = [m for s in report.pairs for m in s.misses]
        if misses:
            lines.append("## Pair misses")
            lines.append("")
            for m in misses[:80]:
                lines.append(
                    f"- {m.language} `{m.sentence}`: {m.source!r} → {m.got!r}"
                )
            if len(misses) > 80:
                lines.append(f"- …and {len(misses) - 80} more")
            lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return report
