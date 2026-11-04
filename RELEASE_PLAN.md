# Release plan

When squirrelator's next release is due, and what it waits for. It follows
the SquirrelGo release rules (LanguageStudentDesk `docs/RELEASES.md`): Claude
prepares a **draft** GitHub Release, the owner clicks **Publish**, and tags
are never moved, reused or deleted.

## Next: v0.1.0

The first release that reads its language data from squirrel-lang-data, so
it can be tested with the apps against the same frozen data. `pyproject.toml`
already says 0.1.0; the last tag is v0.0.1.

It's due when all of these are on `main`:

- [ ] **Phase 0** of the roadmap: `AGENTS.md`, CI (pytest, ruff, a syntax
      check of the web app), the PR guard, and golden tests for what works
      today.
- [ ] From **Phase 1**: the `squirrel-lang-data` submodule at `data/`, pinned
      to the published **data v0.1.0** release, with the engine finding it
      through `SQUIRREL_LANG_DATA` or `data/`.
- [ ] CI green on `main`.
- [ ] A release PR adding `release-notes/v0.1.0.md`, with nothing else in it.

The rest of Phase 1 (the full analyze, parse, interlingua, generate and rank
pipeline) and later phases are v0.2.0 and on. They don't hold v0.1.0 back.

## How the draft is made

1. After the release PR merges, run **Actions → Draft release → Run
   workflow** with the version. It runs the tests, builds the wheel and the
   source archive, writes `SHA256SUMS.txt`, and creates or refreshes a
   **draft** release targeting that commit. It never creates or moves a tag.
2. The owner clicks **Publish**, which creates the tag.

## After v0.1.0

While the apps are tested, `data/` only moves to another squirrel-lang-data
release, never to an untagged commit. Fixes ship as v0.1.1 and so on.
