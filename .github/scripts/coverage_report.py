#!/usr/bin/env python3
"""Write the Pipeline meaning-matrix coverage report as Markdown.

Locally:

    python3 .github/scripts/coverage_report.py
    python3 .github/scripts/coverage_report.py -o coverage-report.md

CI uploads the file as a workflow artifact. Numbers are measured from the
pinned data/, never typed by hand (squirrelator #26 / ROADMAP Phase 5).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from squirrelator.coverage import write_report  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "-o", "--output",
        default="coverage-report.md",
        help="Markdown file to write (default: coverage-report.md)",
    )
    ap.add_argument(
        "--data",
        default=None,
        help="squirrel-lang-data checkout (default: data/ or SQUIRREL_LANG_DATA)",
    )
    args = ap.parse_args(argv)
    report = write_report(args.output, root=args.data)
    print(f"Wrote {args.output} ({len(report.columns)} columns).")
    for c in report.columns:
        bar = "yes" if c.meets_alpha_bar(report.bar) else "no"
        print(
            f"  {c.language}: {c.to_english}/{c.rows} →en, "
            f"{c.from_english}/{c.rows} en→, bar={bar}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
