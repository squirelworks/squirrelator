"""Regression report (ROADMAP Phase 5): golden always; pairs when data has them."""

import pytest

from squirrelator.regression import (
    load_pair_fixtures,
    measure_golden,
    measure_pairs,
    pair_tests_dir,
    write_report,
)


def test_pair_tests_skip_when_absent():
    """No hard fail when the data pin has no testing/translation-pairs/ yet."""
    path = pair_tests_dir()
    if path is None:
        assert load_pair_fixtures() == []
        return
    fixtures = load_pair_fixtures(path)
    assert fixtures, f"expected translation-pair-tests/1 files in {path}"


def test_pair_suites_pass_when_present():
    if pair_tests_dir() is None:
        pytest.skip("testing/translation-pairs/ not in this data pin")
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
    assert "Golden translations" in text
    assert report.golden.total > 0
    if report.pairs:
        assert "Pipeline pair fixtures" in text
        assert report.pair_tests
    else:
        assert "none in this data pin" in text or "No pair fixtures" in text
