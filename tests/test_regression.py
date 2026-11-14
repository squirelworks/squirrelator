"""Regression report (ROADMAP Phase 5): golden + TL pair accepts."""

import pytest

from squirrelator.regression import (
    load_pair_fixtures,
    measure_golden,
    measure_pairs,
    tl_tests_dir,
    write_report,
)


def test_tl_tests_are_reachable():
    path = tl_tests_dir()
    assert path is not None and path.is_dir(), (
        "LanguageStudentDesk translation-learner/tests not found. "
        "Set SQUIRREL_TL_TESTS or check the repo out beside squirrelator."
    )
    fixtures = load_pair_fixtures(path)
    assert fixtures, f"no translation-pair-tests/1 files in {path}"
    langs = {f["language"] for f in fixtures}
    assert "japanese" in langs and "chinese" in langs


def test_pair_suites_pass_on_the_pinned_data():
    if tl_tests_dir() is None:
        pytest.skip("LanguageStudentDesk TL tests not checked out")
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
    if tl_tests_dir() is None:
        pytest.skip("LanguageStudentDesk TL tests not checked out")
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
    assert "translation-learner/tests" in report.tl_tests.replace("\\", "/")
