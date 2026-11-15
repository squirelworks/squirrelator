#!/usr/bin/env python3
"""Write the fuller-pair + golden regression report as Markdown.

Locally:

    python3 .github/scripts/regression_report.py
    python3 .github/scripts/regression_report.py -o regression-report.md

CI uploads the file as a workflow artifact (ROADMAP Phase 5).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from squirrelator.regression import write_report  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "-o", "--output",
        default="regression-report.md",
        help="Markdown file to write (default: regression-report.md)",
    )
    args = ap.parse_args(argv)
    report = write_report(args.output)
    pair_pass = sum(s.passed for s in report.pairs)
    pair_total = sum(s.total for s in report.pairs)
    print(
        f"Wrote {args.output}: golden {report.golden.passed}/{report.golden.total}, "
        f"pairs {pair_pass}/{pair_total} across {len(report.pairs)} languages."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
