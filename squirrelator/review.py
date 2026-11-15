"""Meaning-matrix columns that keep the alpha label until a person reviews them.

The coverage bar (#26, squirrelator.coverage) measures whether the Pipeline
round-trips a column's rows. It can't tell whether those rows are right. The
columns below clear the bar, but their squirrel-lang-data column notes say
some rows are short composed phrases rather than cited forms, and their
review logs (languages/<id>/REVIEW.md) record only mechanical checks so far.
The owner decided they stay alpha until a person has reviewed them.

TODO(LanguageStudentDesk#198): squirrel-lang-data review logs don't yet
record whether a person or only a script did the review. Once they do, read
that from the data instead of keeping this list, and delete this module.

Keep the keys alphabetical. Remove a column only after a person's review is
logged in its squirrel-lang-data REVIEW.md.
"""

from __future__ import annotations

PENDING_HUMAN_REVIEW: dict[str, str] = {
    "aramaic": "Column notes say some classroom phrases are composed.",
    "cherokee": "Column notes say some rows use short composed phrases.",
    "inuktitut": "Column notes say modern loanwords are thin.",
    "manipuri": "Column notes say rows without an in-repo citation use uncited phrasing.",
    "tamazight": "Column notes say some rows use stand-in words (rice as couscous).",
}


def pending_human_review(language: str) -> bool:
    """True while this column waits for a person's review (keeps alpha on)."""
    return language in PENDING_HUMAN_REVIEW
