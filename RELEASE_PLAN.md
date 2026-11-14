# Release plan

When squirrelator's next release is due, and what it waits for. It follows
the SquirrelGo release rules (LanguageStudentDesk `docs/RELEASES.md`): Claude
prepares a **draft** GitHub Release, the owner clicks **Publish**, and tags
are never moved, reused or deleted.

## Released

- [x] **v0.1.0** (2026-11-04): Phase 0, the `data/` submodule pinned to
      data v0.1.0, golden tests and CI.

## Drafted, not published: v0.1.1

- [x] `data/` moved to squirrel-lang-data **v0.1.4** (#41).
- [x] Release PR: `release-notes/v0.1.1.md` and the version raised (#42).
- [x] Phone app ready for Google Play: store listing, launcher icon, signed
      bundle (#43).
- [x] Draft created by **Draft release**.
- [ ] The owner publishes. **Not done, and the draft is now stale:** `main`
      has moved on to data **v0.1.5** (#49) with more engine work (#44–#49),
      so publishing the draft as it stands ships the older data and engine.

## Next (open): refresh, then publish

Since the draft, on `main`: English as the source reads contractions and a
word's row meaning (#48), code explained with the code pack's English rows
(#46), a bare 今日は reads as hello (#47), a bare Klingon jatlh is third
person (#45), the Cloud Agent setup notes (#44), and data **v0.1.5** with
French, German and Italian columns and Latin following its fuller column (#49).

The owner picks one; nothing is published without the owner's "release":

1. **Keep the version (suggested).** The `v0.1.1` tag doesn't exist yet, so
   one release PR updates `release-notes/v0.1.1.md` to name data v0.1.5 and
   add the items above, with nothing else in it. Then re-run **Draft
   release** with `v0.1.1`; it refreshes the existing draft to the new
   `main` commit.
2. **A new version.** A release PR raises the version to 0.1.2 in
   `pyproject.toml` and `squirrelator.__version__` and adds
   `release-notes/v0.1.2.md`; the v0.1.1 draft stays unpublished.

Either way:

- [ ] `data/` pins the same squirrel-lang-data tag as LanguageStudentDesk
      (both v0.1.5 today).
- [ ] CI green on `main`.
- [ ] The release PR, then **Actions → Draft release → Run workflow**, then
      the owner publishes.

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
