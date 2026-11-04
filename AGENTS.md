# Rules for agents working in this repo

squirrelator is the translation engine of the LanguageStudentDesk (LSD)
environment. A worker thread opens PRs and a separate merger thread reviews and
squash-merges them. This file is the doctrine in short. How merging and
conflicts work is in `.github/MERGING.md`.

## Doctrine

1. **One seam per PR.** One pipeline stage, one language pair, one code
   target or one UI change. Mixed PRs are held.
2. **Share, don't fork.** Language content (meanings, sentences, word banks,
   glosses, language rules, programming keyword maps) lives in
   `squirelworks/squirrel-lang-data`, pulled in as a submodule at `data/`.
   Never keep or edit a copy here. Data changes are a PR to the data repo,
   then a separate PR here that bumps the submodule to a commit on its `main`.
3. **Data before shells.** Engine code reads data files. It doesn't hardcode
   words in `if` chains.
4. **Twins.** The Tk GUI (`squirrelator_gui.py`) and the web app (`app/`)
   offer the same features from the same engine and data. If one can't, the
   PR says why.
5. **No implementation notes in the UI.** No file paths, module names or rule
   ids in user-facing output, except in a Breakdown or Why view that explains
   the translation in plain words.
6. **Binaries go to Releases.** No committed executables, wheels, APKs, model
   blobs or downloaded corpora. The PR guard rejects them.

## Translation rules

- Rule-based and deterministic: the same input, data version and settings
  always give the same output. No online translators or LLM APIs at run time.
- Never invent. Unknown words and structures are marked unknown.
- Return alternatives when the source leaves something open.
- Every language pair is labeled **alpha** until its test set passes.
- `translate(source, from_lang, to_lang, *, style=None)` keeps working,
  because LSD calls it. New features go behind new functions or keyword
  arguments. A breaking change needs the owner's OK.
- Generated code in a language CI can run is run in the tests and its output
  checked. A sentence that can't be mapped becomes a comment saying so.

## Writing

- READMEs have no hardcoded counts or full lists of supported languages.
- Human languages are listed alphabetically. Programming languages go modern
  and popular, then older and legacy, then joke, A to Z inside each group.
- Every data source is cited with its license in the PR body and in
  `languages/SOURCES.md`.
- Content is CC BY-SA 4.0. Tools and code are MIT.

## If you open PRs

1. Branch from the latest `origin/main` for every PR. The base is always
   `main`; never stack PRs.
2. Start the body with a `Scope:` line naming the files or folders the PR may
   change, e.g. `Scope: squirrelator/translator.py, tests/`. The guard fails
   the PR if it changes anything else. Then `Part of #<issue>` if there is
   one, a summary, and the checks you ran.
3. Before pushing, run:

       python -m pytest -q
       ruff check .
       python3 .github/scripts/pr_guard.py --base origin/main --head HEAD

4. When your PR conflicts with main, fix it yourself with
   `git merge origin/main`, combining both sides. Never `-s ours`, `-X ours`
   or `git checkout --ours .`. Never force-push or rewrite history.

## If you merge PRs

1. Merge only when every check is green on the head commit, including
   **PR guard / guard**, and the "Merge verdict" comment says
   **SAFE TO MERGE**.
2. Never resolve a conflict in GitHub's web editor, and never pick the
   branch's side. Skip a conflicting PR; its author fixes it.
3. Use "Squash and merge" only. Never override branch protection.

## Releases

Claude prepares a **draft** GitHub Release; the owner clicks Publish. Tags
are never created, moved, reused or deleted by hand. CI on PRs and pushes
only checks and builds; it never uploads build output. See
`RELEASE_PLAN.md`.
