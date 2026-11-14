"""Pipeline coverage of the meaning-matrix columns.

For every language column, count how many of its rows come back as the top
English result in each direction (column → English, and English → column).
The numbers are generated, never hand-edited into docs or issues.

A pair meets the alpha bar in #26 when at least ALPHA_BAR of its column
rows match top-1 both ways. This module reports that; it does not flip
any alpha label in the product (that is a follow-up once the report is the
source of truth).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .matrix import Matrix, matrix
from .pipeline import run
from .pipeline.generate import render

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


def measure_column(language: str, mx: Matrix | None = None, *, root=None) -> ColumnCoverage:
    """Count top-1 hits for one column against English both ways."""
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
    return ColumnCoverage(
        language,
        len(cols),
        to_en,
        from_en,
        tuple(to_misses),
        tuple(from_misses),
    )


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
        "This report does not change product alpha labels.",
        "",
    ]
    if report.data_pin:
        lines += [f"Data pin: `{report.data_pin}`", ""]
    lines += [
        "| Column | Rows | → en (top 1) | en → (top 1) | ≥ bar |",
        "|---|---|---|---|---|",
    ]
    for c in report.columns:
        flag = "yes" if c.meets_alpha_bar(report.bar) else "no"
        lines.append(
            f"| {c.language} | {c.rows} | {c.to_english}/{c.rows} | "
            f"{c.from_english}/{c.rows} | {flag} |"
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
