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
      (#49), then **v0.1.6**.
- [x] Release PR: `release-notes/v0.1.1.md` and the version raised (#42).
- [x] Phone app ready for Google Play: store listing, launcher icon, signed
      bundle (#43).
- [x] Release notes refreshed for data **v0.1.5** and the engine work that
      landed since the first draft (#44–#51): English as the source (#48),
      code explained with the code pack (#46), bare 今日は (#47), bare Klingon
      jatlh as third person (#45), Cloud Agent setup notes (#44), the v0.1.5
      pin (#49), and the coverage report plus Chinese/Klingon miss fixes
      (#51).
- [x] Draft created by **Draft release** (against older `main`).
- [x] `v0.1.1` published (on the older release-PR commit). Further ship work
      moved to **v0.1.2**.

## Next (open): publish v0.1.2 from current main

`v0.1.1` is published on the wrong commit. Remaining steps for **v0.1.2**:

- [x] Version raised to 0.1.2 and `release-notes/v0.1.2.md` added (#129).
- [x] `data/` pins the same squirrel-lang-data tag as LanguageStudentDesk
      (**v0.1.6**, #131), with English do-support / segmentation follow-ups
      (#133, #134).
- [x] Release notes refreshed for data **v0.1.6** and those engine fixes.
- [x] CI green on `main`.
- [x] **v0.1.2 draft** refreshed onto current `main` (data **v0.1.6** /
      `73b5ace`, do-support #133/#134). Prefer **Actions → Draft release →
      Run workflow** with `v0.1.2` if the draft needs another refresh.
- [ ] The owner publishes. Do not publish any older draft that still named
      data v0.1.5.

This is also the phone app's first Google Play build. Once it's published,
LanguageStudentDesk's **squirrelator Play testing** workflow sends it to
internal testing within the hour and sets the store listing; a hand-started
run promotes it to closed testing (`native/README.md`, "Google Play"). The
app's version comes from `pyproject.toml`, so the release PR doesn't touch
`native/`.

## How the draft is made

1. After the release PR merges, run **Actions → Draft release → Run
   workflow** with the version. It runs the tests, builds the wheel and the
   source archive, and creates or refreshes a **draft** release targeting
   that commit. Then it builds the phone app's release APK
   (`Squirrelator.apk`) and attaches it, and finally writes `SHA256SUMS.txt`
   over every file on the draft. It never builds or attaches an AAB, and it
   never creates or moves a tag.
2. The owner clicks **Publish**, which creates the tag.

## Between releases

While the apps are tested, `data/` only moves to another squirrel-lang-data
release, never to an untagged commit. Fixes ship as v0.1.1 and so on.
