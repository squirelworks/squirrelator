"""Pipeline coverage of the meaning-matrix columns.

For every language column, count how many of its rows come back as the top
English result in each direction (column → English, and English → column).
The numbers are generated, never hand-edited into docs or issues.

A pair meets the alpha bar in #26 when at least ALPHA_BAR of its column
rows match top-1 both ways. Product Pipeline alpha labels follow that bar
via pair_is_alpha(), which reads the same measurements as this report. A
column listed in squirrelator.review stays alpha even at the bar, until a
person has reviewed it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .matrix import Matrix, matrix
from .pipeline import run
from .pipeline.generate import render
from .review import pending_human_review

# Issue #26: drop "alpha" when at least this share of column rows come back
# as the top English result in both directions.
ALPHA_BAR = 0.90

@dataclass(frozen=True)
class ColumnCoverage:
    """Top-1 round-trip counts for one meaning-matrix column."""

    language: str
    rows: int
    to_english: int
    from_english: int
    to_english_misses: tuple[str, ...] = ()
    from_english_misses: tuple[str, ...] = ()

    @property
    def to_english_rate(self) -> float:
        return self.to_english / self.rows if self.rows else 0.0

    @property
    def from_english_rate(self) -> float:
        return self.from_english / self.rows if self.rows else 0.0

    def meets_alpha_bar(self, bar: float = ALPHA_BAR) -> bool:
        """True when both directions clear the #26 threshold."""
        return (
            self.rows > 0
            and self.to_english_rate >= bar
            and self.from_english_rate >= bar
        )


@dataclass(frozen=True)
class CoverageReport:
    columns: tuple[ColumnCoverage, ...]
    data_pin: str = ""
    bar: float = ALPHA_BAR

    def passing(self) -> tuple[ColumnCoverage, ...]:
        return tuple(c for c in self.columns if c.meets_alpha_bar(self.bar))


# Per-process cache of column measurements. Cleared by clear_coverage_cache().
# While a column is being measured, pair_is_alpha must not re-enter measure
# (measure_column calls pipeline.run, which asks for alpha).
_column_cache: dict[tuple[str, str], ColumnCoverage] = {}
_measuring: set[tuple[str, str]] = set()


def _column_text(rendering) -> str:
    return render([t for t, _, _ in rendering.tokens], rendering.sep, rendering.end)


def _english_targets(row) -> set[str]:
    return {row.en, *row.also}


def _data_pin(root: Path) -> str:
    """Tag or short SHA of the squirrel-lang-data checkout, when git knows it."""
    import subprocess

    try:
        out = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            cwd=root, check=True, capture_output=True, text=True,
        ).stdout.strip()
        return out
    except (OSError, subprocess.CalledProcessError):
        return root.name


def _root_key(root=None) -> str:
    """Stable cache key for a data checkout (or the default lookup)."""
    from .data import DataNotFound, data_dir

    try:
        return str(data_dir(root).resolve())
    except DataNotFound:
        return "" if root is None else str(Path(root).resolve())


def clear_coverage_cache() -> None:
    """Drop cached column measurements (tests and a data-pin change)."""
    _column_cache.clear()
    _measuring.clear()


def measure_column(language: str, mx: Matrix | None = None, *, root=None) -> ColumnCoverage:
    """Count top-1 hits for one column against English both ways."""
    key = (language, _root_key(root))
    _measuring.add(key)
    try:
        mx = mx or matrix(root)
        cols = mx.columns.get(language, {})
        to_en = from_en = 0
        to_misses: list[str] = []
        from_misses: list[str] = []
        for row_id, rendering in sorted(cols.items()):
            row = mx.rows[row_id]
            source = _column_text(rendering)
            got_en = run(source, language, "english", root=root).text
            if got_en in _english_targets(row):
                to_en += 1
            else:
                to_misses.append(row_id)
            got_lang = run(row.en, "english", language, root=root).text
            if got_lang == source:
                from_en += 1
            else:
                from_misses.append(row_id)
        result = ColumnCoverage(
            language,
            len(cols),
            to_en,
            from_en,
            tuple(to_misses),
            tuple(from_misses),
        )
        _column_cache[key] = result
        return result
    finally:
        _measuring.discard(key)


def measure_all(*, root=None) -> CoverageReport:
    """Measure every meaning-matrix column present in the data checkout."""
    from .data import DataNotFound, data_dir

    mx = matrix(root)
    columns = tuple(
        measure_column(lang, mx, root=root) for lang in sorted(mx.columns)
    )
    pin = ""
    try:
        pin = _data_pin(data_dir(root).resolve())
    except DataNotFound:
        pass
    return CoverageReport(columns, data_pin=pin, bar=ALPHA_BAR)


def column_meets_alpha_bar(
    language: str,
    *,
    root=None,
    bar: float = ALPHA_BAR,
    report: CoverageReport | None = None,
) -> bool:
    """True when this language's meaning-matrix column clears the #26 bar.

    English is the reference side and has no column; it always counts as
    meeting the bar. A language with no column (or an empty one) does not.
    Uses the same measure_column() path as the CI report, with a per-process
    cache so ordinary translations do not re-measure every call.
    """
    if language == "english":
        return True
    if report is not None:
        for c in report.columns:
            if c.language == language:
                return c.meets_alpha_bar(bar)
        return False
    key = (language, _root_key(root))
    if key in _measuring:
        # measure_column is on the stack (via pipeline.run); alpha is unused
        # for the .text checks, so skip re-entry.
        return False
    if key not in _column_cache:
        measure_column(language, root=root)
    cached = _column_cache.get(key)
    return bool(cached and cached.meets_alpha_bar(bar))


def pair_is_alpha(
    from_lang: str,
    to_lang: str,
    *,
    root=None,
    bar: float = ALPHA_BAR,
    report: CoverageReport | None = None,
) -> bool:
    """Whether a Pipeline pair still carries the alpha label (#26 / P2.1).

    Same-language is never alpha. Otherwise every non-English side must
    clear the coverage bar; if any side has no column or is under the bar,
    the pair stays alpha. A side still waiting for a person's review
    (squirrelator.review) keeps the pair alpha even at the bar.
    """
    if from_lang == to_lang:
        return False
    sides = {from_lang, to_lang} - {"english"}
    if not sides:
        return False
    if any(pending_human_review(lang) for lang in sides):
        return True
    return not all(
        column_meets_alpha_bar(lang, root=root, bar=bar, report=report)
        for lang in sides
    )


def format_markdown(report: CoverageReport) -> str:
    """A Markdown table matching the shape used in #26, plus the alpha bar."""
    bar_pct = int(round(report.bar * 100))
    lines = [
        "# Pipeline coverage report",
        "",
        "Generated from the pinned squirrel-lang-data meaning-matrix columns.",
        "Each cell is rows whose top Pipeline result matches the row "
        "(column → English: the row's English or an `also` wording; "
        "English → column: the column's own rendering).",
        "",
        f"Alpha bar (#26): ≥{bar_pct}% top-1 both ways. "
        "Pipeline product alpha labels follow this bar "
        "(squirrelator.coverage.pair_is_alpha), except that a column "
        "waiting for a person's review stays alpha (squirrelator.review).",
        "",
    ]
    if report.data_pin:
        lines += [f"Data pin: `{report.data_pin}`", ""]
    lines += [
        "| Column | Rows | → en (top 1) | en → (top 1) | ≥ bar | Alpha |",
        "|---|---|---|---|---|---|",
    ]
    for c in report.columns:
        meets = c.meets_alpha_bar(report.bar)
        flag = "yes" if meets else "no"
        if not meets:
            alpha = "yes"
        elif pending_human_review(c.language):
            alpha = "yes (awaiting human review)"
        else:
            alpha = "no"
        lines.append(
            f"| {c.language} | {c.rows} | {c.to_english}/{c.rows} | "
            f"{c.from_english}/{c.rows} | {flag} | {alpha} |"
        )
    passing = report.passing()
    lines += [
        "",
        f"Columns at the bar: {len(passing)} of {len(report.columns)}"
        + (f" ({', '.join(c.language for c in passing)})" if passing else "")
        + ".",
        "",
    ]
    misses = [c for c in report.columns if c.to_english_misses or c.from_english_misses]
    if misses:
        lines += ["## Misses", ""]
        for c in misses:
            if c.to_english_misses:
                lines.append(
                    f"- {c.language} → en: {', '.join(c.to_english_misses)}"
                )
            if c.from_english_misses:
                lines.append(
                    f"- en → {c.language}: {', '.join(c.from_english_misses)}"
                )
        lines.append("")
    return "\n".join(lines)


def write_report(path: str | Path, *, root=None) -> CoverageReport:
    """Measure every column and write the Markdown report to path."""
    report = measure_all(root=root)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_markdown(report), encoding="utf-8")
    return report
