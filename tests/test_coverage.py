"""Pipeline coverage report: formatting, the #26 alpha bar, and a smoke run."""

import pytest

from squirrelator import data
from squirrelator.coverage import (
    ALPHA_BAR,
    ColumnCoverage,
    CoverageReport,
    format_markdown,
    measure_column,
    write_report,
)

try:
    data.data_dir()
except data.DataNotFound:
    pytest.skip("squirrel-lang-data not checked out", allow_module_level=True)


def test_alpha_bar_matches_issue_26():
    assert ALPHA_BAR == 0.90


def test_meets_alpha_bar_both_ways():
    ok = ColumnCoverage("hangul", 100, 90, 90)
    assert ok.meets_alpha_bar()
    low_to = ColumnCoverage("x", 100, 89, 100)
    assert not low_to.meets_alpha_bar()
    low_from = ColumnCoverage("x", 100, 100, 89)
    assert not low_from.meets_alpha_bar()
    empty = ColumnCoverage("x", 0, 0, 0)
    assert not empty.meets_alpha_bar()


def test_format_markdown_table_shape():
    report = CoverageReport(
        (
            ColumnCoverage("chinese", 103, 101, 103, ("eat-food", "what-time"), ()),
            ColumnCoverage("hangul", 103, 103, 103),
        ),
        data_pin="v0.1.5",
        bar=0.90,
    )
    md = format_markdown(report)
    assert md.startswith("# Pipeline coverage report")
    assert "| Column | Rows | → en (top 1) | en → (top 1) | ≥ bar |" in md
    assert "| chinese | 103 | 101/103 | 103/103 | yes |" in md
    assert "| hangul | 103 | 103/103 | 103/103 | yes |" in md
    assert "Columns at the bar: 2 of 2" in md
    assert "chinese → en: eat-food, what-time" in md
    assert "This report does not change product alpha labels." in md


def test_measure_klingon_column_smoke(root):
    # Klingon is the smallest column; a full pass stays cheap in the suite.
    c = measure_column("klingon", root=root)
    assert c.language == "klingon"
    assert c.rows >= 1
    assert 0 <= c.to_english <= c.rows
    assert 0 <= c.from_english <= c.rows
    # Known open misses from #26; the report must still count the rest.
    assert c.to_english >= c.rows - 2


def test_write_report_produces_every_column(root, tmp_path):
    out = tmp_path / "coverage-report.md"
    report = write_report(out, root=root)
    text = out.read_text(encoding="utf-8")
    assert report.columns
    assert len(report.columns) == len({c.language for c in report.columns})
    for c in report.columns:
        assert f"| {c.language} |" in text
    assert report.data_pin
    assert "v0.1.5" in report.data_pin or len(report.data_pin) >= 7
