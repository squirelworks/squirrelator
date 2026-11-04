# How merging works here, and why it's safe

squirrelator uses the same merge setup as LanguageStudentDesk.

## What goes wrong without it

When several agents open PRs at once, the second PR to touch a file
conflicts. If someone resolves that conflict by keeping the branch's side
(GitHub's conflict editor, "accept current", `-s ours`), the merge commit
looks normal but its files are the branch's old files. The PR's diff now
shows everything main gained as deleted or reverted, and "Squash and merge"
applies exactly that. LanguageStudentDesk lost about 1,300 files this way
once.

A branch that is merely *behind* main is fine: GitHub squashes with a
three-way merge. The problem is always a merge commit that threw main's
side away.

## The guard

`.github/workflows/pr-guard.yml` runs `.github/scripts/pr_guard.py` on every
PR, on every push and whenever the body or labels change. It fails when:

1. **The base isn't `main`.** Stacked PRs aren't allowed.
2. **A file changes only through a merge commit.** Every file in the diff
   must have been touched by one of the branch's own commits. Otherwise
   main's version was thrown away.
3. **A file is outside the PR's `Scope:` line.** Without the line, the guard
   prints the folders it inferred and doesn't enforce them.
4. **A binary or large file is added or changed**: executables, archives,
   wheels, APKs, model files, databases, any file over 1 MB, or a binary that
   isn't a small image or font. The `binaries-ok` label overrides this, for
   a reviewed exception.
5. **More than 100 files are deleted**, unless the PR has the `deletions-ok`
   label.

The check runs main's copy of the script, so a PR can't loosen its own
check. It posts one comment, updated on every run, that starts with
**Merge verdict: SAFE TO MERGE** or **Merge verdict: DO NOT MERGE**.

Run it locally before pushing:

    python3 .github/scripts/pr_guard.py --base origin/main --head HEAD

## Merging main into your branch

When your PR conflicts with main:

    git fetch origin main
    git merge origin/main

Resolve each conflict by combining both sides: keep main's new lines and
yours. For a file outside your PR's scope, take main's version:

    git checkout origin/main -- <file>

For a version number, take the higher one. For a submodule pointer, take
main's unless bumping it is your PR's seam. Then run the tests and the guard,
and push a normal commit. Never `git merge -s ours`, `-X ours` or
`git checkout --ours .`, never force-push, and never press GitHub's
"Resolve conflicts" button.

`.github/workflows/pr-conflicts.yml` runs after every push to main. Any open
PR that now conflicts gets the `merge-conflict` label and a comment asking
its author to merge main. The label clears itself once the conflict is gone.

## One-time settings (repo owner)

After the guard is on main:

1. **Settings → Rules → Rulesets → New ruleset → New branch ruleset**.
   Name it `Protect main` and set **Enforcement status** to **Active**.
2. **Target branches → Add target → Include default branch**.
3. Tick **Require status checks to pass**, then add **guard** and the CI
   checks (**tests (3.10)**, **tests (3.12)**, **lint**, **web**). Leave
   **Require branches to be up to date before merging** unticked.
4. Keep **Block force pushes** and **Restrict deletions** ticked.
5. Optional, in **Settings → General → Pull Requests**: untick **Allow merge
   commits** and **Allow rebase merging**, so only "Squash and merge" is
   offered.
