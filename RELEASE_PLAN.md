# Release plan

When squirrelator's next release is due, and what it waits for. It follows
the SquirrelGo release rules (LanguageStudentDesk `docs/RELEASES.md`): Claude
prepares a **draft** GitHub Release, the owner clicks **Publish**, and tags
are never moved, reused or deleted.

## Released

- [x] **v0.1.0** (2026-11-04): Phase 0, the `data/` submodule pinned to
      data v0.1.0, golden tests and CI.

- [x] **v0.1.1** (2026-11-15): published, but the tag pointed at the older
      release-PR commit (`560ea3e`), not current `main`.
- [ ] **v0.1.2**: ship from current `main` (Phase 4 intent fills and later
      notes).

## Was: drafted v0.1.1

- [x] `data/` moved to squirrel-lang-data **v0.1.4** (#41), then **v0.1.5**
      (#49).
- [x] Release PR: `release-notes/v0.1.1.md` and the version raised (#42).
- [x] Phone app ready for Google Play: store listing, launcher icon, signed
      bundle (#43).
- [x] Release notes refreshed for data **v0.1.5** and the engine work that
      landed since the first draft (#44–#51): English as the source (#48),
      code explained with the code pack (#46), bare 今日は (#47), bare Klingon
      jatlh as third person (#45), Cloud Agent setup notes (#44), the v0.1.5
      pin (#49), and the coverage report plus Chinese/Klingon miss fixes
      (#51).
- [x] Draft created by **Draft release** (against older `main`; refresh it
      after the notes PR merges).
- [ ] Re-run **Actions → Draft release → Run workflow** with `v0.1.1` so the
      draft targets current `main`.
- [ ] The owner publishes. Nothing is published without the owner's
      "release".

## Next (open): publish v0.1.2 from current main

`v0.1.1` is published on the wrong commit. Remaining steps for **v0.1.2**:

- [x] `data/` pins the same squirrel-lang-data tag as LanguageStudentDesk
      (both v0.1.5 today).
- [ ] CI green on `main`.
- [ ] **Actions → Draft release → Run workflow** with `v0.1.1` (refreshes
      the existing draft to the new `main` commit), then the owner publishes.

If the owner prefers a new version number instead (v0.1.2), leave the
v0.1.1 draft unpublished and open a release PR that raises the version in
`pyproject.toml` and `squirrelator.__version__` and adds
`release-notes/v0.1.2.md`.

This is also the phone app's first Google Play build. Once it's published,
LanguageStudentDesk's **squirrelator Play testing** workflow sends it to
internal testing within the hour and sets the store listing; a hand-started
run promotes it to closed testing (`native/README.md`, "Google Play"). The
app's version comes from `pyproject.toml`, so the release PR doesn't touch
`native/`.

## How the draft is made

1. After the release PR merges, run **Actions → Draft release → Run
   workflow** with the version. It runs the tests, builds the wheel and the
   source archive, writes `SHA256SUMS.txt`, and creates or refreshes a
   **draft** release targeting that commit. It never creates or moves a tag.
2. The owner clicks **Publish**, which creates the tag.

## Between releases

While the apps are tested, `data/` only moves to another squirrel-lang-data
release, never to an untagged commit. Fixes ship as v0.1.1 and so on.
