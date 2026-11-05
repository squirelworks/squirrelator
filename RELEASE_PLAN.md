# Release plan

When squirrelator's next release is due, and what it waits for. It follows
the SquirrelGo release rules (LanguageStudentDesk `docs/RELEASES.md`): Claude
prepares a **draft** GitHub Release, the owner clicks **Publish**, and tags
are never moved, reused or deleted.

## Released

- [x] **v0.1.0** (2026-11-04): Phase 0, the `data/` submodule pinned to
      data v0.1.0, golden tests and CI.

Since then, on `main`: the whole Phase 1 pipeline (Analyze, Parse,
Interlingua, Generate, Rank), `engine="auto"` as the default with the
Pipeline as a second opinion for Latin and Klingon, Latin and English
inflections from the data, the `native/` Compose app with a test APK
workflow, and `data/` at the **v0.1.3** tag (#38). See `ROADMAP.md`.

## Next: v0.1.1

- [ ] Optionally wait for squirrel-lang-data **v0.1.4** and a one-seam PR here
      moving `data/` to it (the code pack, Latin and English inflection
      tables, the grammar expansion). If the owner wants v0.1.1 sooner, it
      ships on v0.1.3.
- [ ] `data/` pins the same squirrel-lang-data tag as LanguageStudentDesk.
- [ ] CI green on `main`.
- [ ] A release PR adding `release-notes/v0.1.1.md` (and raising the version
      in `pyproject.toml` and `squirrelator.__version__`), with nothing else
      in it.
- [ ] **Actions → Draft release → Run workflow** with `v0.1.1`.
- [ ] The owner publishes. Nothing is released until the owner says
      "release".

v0.1.1 is also the phone app's first Google Play build. Publishing the
release sends it to internal testing, and a hand-started promotion moves it
to closed testing (`native/README.md`, "Google Play"). That needs the Play
and upload-key secrets in this repo first. The app's version comes from
`pyproject.toml`, so the release PR doesn't touch `native/`.

## How the draft is made

1. After the release PR merges, run **Actions → Draft release → Run
   workflow** with the version. It runs the tests, builds the wheel and the
   source archive, writes `SHA256SUMS.txt`, and creates or refreshes a
   **draft** release targeting that commit. It never creates or moves a tag.
2. The owner clicks **Publish**, which creates the tag.

## Between releases

While the apps are tested, `data/` only moves to another squirrel-lang-data
release, never to an untagged commit. Fixes ship as v0.1.1 and so on.
