"""Regression fixtures and report (ROADMAP Phase 5)."""

import pytest

from squirrelator.regression import (
    REGRESSION_DIR,
    load_pair_fixtures,
    measure_golden,
    measure_pairs,
    write_report,
)


def test_pair_fixtures_are_present_and_named():
    fixtures = load_pair_fixtures()
    assert fixtures, "expected tests/regression/*-english.json"
    langs = {f["language"] for f in fixtures}
    assert "japanese" in langs and "chinese" in langs and "klingon" in langs
    for path in REGRESSION_DIR.glob("*-english.json"):
        assert path.name.endswith("-english.json")


def test_pair_suites_pass_on_the_pinned_data():
    try:
        from squirrelator import data
        data.data_dir()
    except Exception:
        pytest.skip("squirrel-lang-data not checked out")
    for suite in measure_pairs():
        assert suite.passed == suite.total, (
            f"{suite.language}: {suite.passed}/{suite.total}; "
            f"misses={[m.sentence for m in suite.misses]}"
        )


def test_golden_suite_still_matches():
    g = measure_golden()
    assert g.passed == g.total, f"golden misses: {g.misses[:5]}"


def test_write_report_makes_markdown(tmp_path):
    try:
        from squirrelator import data
        data.data_dir()
    except Exception:
        pytest.skip("squirrel-lang-data not checked out")
    out = tmp_path / "regression-report.md"
    report = write_report(out)
    text = out.read_text(encoding="utf-8")
    assert "Golden translations" in text and "Pipeline pair fixtures" in text
    assert report.golden.total > 0 and report.pairs
