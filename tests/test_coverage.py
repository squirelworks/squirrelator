"""Pipeline coverage report: formatting, the #26 alpha bar, and a smoke run."""

import pytest

from squirrelator import data
from squirrelator.coverage import (
    ALPHA_BAR,
    ColumnCoverage,
    CoverageReport,
    clear_coverage_cache,
    column_meets_alpha_bar,
    format_markdown,
    measure_column,
    pair_is_alpha,
    write_report,
)
from squirrelator.review import PENDING_HUMAN_REVIEW, pending_human_review

try:
    data.data_dir()
except data.DataNotFound:
    pytest.skip("squirrel-lang-data not checked out", allow_module_level=True)


@pytest.fixture(autouse=True)
def _fresh_coverage_cache():
    clear_coverage_cache()
    yield
    clear_coverage_cache()


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


def test_pair_is_alpha_follows_report_not_a_hand_list():
    report = CoverageReport(
        (
            ColumnCoverage("hangul", 100, 100, 100),
            ColumnCoverage("klingon", 17, 15, 16),  # under 90%
        ),
        bar=0.90,
    )
    assert not pair_is_alpha("english", "hangul", report=report)
    assert not pair_is_alpha("hangul", "english", report=report)
    assert pair_is_alpha("english", "klingon", report=report)
    assert pair_is_alpha("hangul", "klingon", report=report)
    assert not pair_is_alpha("hangul", "hangul", report=report)
    assert pair_is_alpha("english", "amharic", report=report)  # no column
    assert column_meets_alpha_bar("english", report=report)
    assert column_meets_alpha_bar("hangul", report=report)
    assert not column_meets_alpha_bar("klingon", report=report)


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
    assert "| Column | Rows | → en (top 1) | en → (top 1) | ≥ bar | Alpha |" in md
    assert "| chinese | 103 | 101/103 | 103/103 | yes | no |" in md
    assert "| hangul | 103 | 103/103 | 103/103 | yes | no |" in md
    assert "Columns at the bar: 2 of 2" in md
    assert "chinese → en: eat-food, what-time" in md
    assert "pair_is_alpha" in md
    assert "This report does not change product alpha labels." not in md


def test_measure_klingon_column_smoke(root):
    # Klingon is the smallest column; a full pass stays cheap in the suite.
    c = measure_column("klingon", root=root)
    assert c.language == "klingon"
    assert c.rows >= 1
    assert 0 <= c.to_english <= c.rows
    assert 0 <= c.from_english <= c.rows
    # After the #51 miss fixes, Klingon clears the bar on the pinned data;
    # the report must still count every row either way.
    assert c.to_english + len(c.to_english_misses) == c.rows
    assert c.from_english + len(c.from_english_misses) == c.rows


def test_write_report_produces_every_column(root, tmp_path):
    out = tmp_path / "coverage-report.md"
    report = write_report(out, root=root)
    text = out.read_text(encoding="utf-8")
    assert report.columns
    assert len(report.columns) == len({c.language for c in report.columns})
    for c in report.columns:
        assert f"| {c.language} |" in text
    assert report.data_pin
    assert report.data_pin.startswith("v") or len(report.data_pin) >= 7
    # Product alpha for a passing column follows the same measurement,
    # unless the column is still waiting for a person's review.
    for c in report.passing():
        expected = pending_human_review(c.language)
        assert pair_is_alpha("english", c.language, report=report) is expected


def test_pending_review_list_is_sorted_and_names_real_columns(root):
    from squirrelator.matrix import matrix

    names = list(PENDING_HUMAN_REVIEW)
    assert names == sorted(names)
    columns = set(matrix(root).columns)
    for lang, why in PENDING_HUMAN_REVIEW.items():
        assert lang in columns, lang
        assert why.strip()


def test_pending_review_keeps_alpha_at_the_bar():
    report = CoverageReport(
        (
            ColumnCoverage("aramaic", 100, 100, 100),
            ColumnCoverage("hangul", 100, 100, 100),
        ),
        bar=0.90,
    )
    assert pending_human_review("aramaic")
    assert not pending_human_review("hangul")
    # The column clears the bar, but alpha stays until a person reviews it.
    assert column_meets_alpha_bar("aramaic", report=report)
    assert pair_is_alpha("english", "aramaic", report=report)
    assert pair_is_alpha("aramaic", "english", report=report)
    assert pair_is_alpha("hangul", "aramaic", report=report)
    assert not pair_is_alpha("aramaic", "aramaic", report=report)
    assert not pair_is_alpha("english", "hangul", report=report)
    md = format_markdown(report)
    assert "| aramaic | 100 | 100/100 | 100/100 | yes | yes (awaiting human review) |" in md
    assert "| hangul | 100 | 100/100 | 100/100 | yes | no |" in md


def test_pending_review_columns_are_alpha_in_the_pipeline(root):
    from squirrelator.pipeline import run

    for lang in PENDING_HUMAN_REVIEW:
        assert run("hello", "english", lang, root=root).alpha is True, lang
