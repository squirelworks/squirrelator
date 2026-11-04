#!/usr/bin/env python3
"""PR guard: stop a pull request from quietly undoing work on main, or from
bringing in things that don't belong in the repo.

Same guard as LanguageStudentDesk, plus the base and binary checks from the
squirrelator roadmap. Checks, all against the merge base with main (the same
diff GitHub squashes):

1. Base. The PR must target main (--base-ref). Stacked PRs fail.
2. Merge-only changes. Every file the PR changes must have been touched by
   one of the branch's own (non-merge) commits. A file that differs from main
   only because of a merge commit is a lost conflict resolution.
3. Scope. A "Scope:" line in the PR body lists the folders or files the PR
   may change, e.g. "Scope: squirrelator/translator.py, tests/". Any other
   changed file fails. Without the line, the inferred scope is reported but
   not enforced.
4. Binaries and large files. Added or changed files fail if they have a
   build-output, archive, model or database extension, are over SIZE_LIMIT
   bytes, or are binary and not a small image or font. The "binaries-ok"
   label overrides this for a reviewed exception.
5. Mass deletion. Deleting more than DELETE_LIMIT files needs the
   "deletions-ok" label.

Usage: pr_guard.py --base <main ref> --head <branch ref> [--base-ref main]
                   [--body-file F] [--labels a,b]
Locally: python3 .github/scripts/pr_guard.py --base origin/main --head HEAD
"""
import argparse
import fnmatch
import re
import subprocess
import sys

DELETE_LIMIT = 100
LIST_LIMIT = 40
SIZE_LIMIT = 1_000_000
FORBIDDEN = {
    ".7z", ".aab", ".apk", ".bin", ".bz2", ".ckpt", ".db", ".dll", ".dmg", ".dylib",
    ".egg", ".exe", ".gguf", ".gz", ".h5", ".ipa", ".jar", ".msi", ".npy", ".npz",
    ".onnx", ".pickle", ".pkl", ".pt", ".pth", ".pyc", ".rar", ".safetensors", ".so",
    ".sqlite", ".sqlite3", ".tar", ".tgz", ".whl", ".xz", ".zip",
}
BINARY_OK = {".gif", ".ico", ".jpeg", ".jpg", ".otf", ".png", ".ttf", ".webp", ".woff", ".woff2"}


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def parse_scope(body):
    entries = []
    for m in re.finditer(r"^\s*[*_`]*Scope[*_`]*\s*:\s*(.+)$", body or "", re.I | re.M):
        if "<" in m.group(1):  # the template's unfilled placeholder
            continue
        entries += [e.strip("`*_ ") for e in re.split(r"[,\s]+", m.group(1))]
    return [e[2:] if e.startswith("./") else e for e in entries if e]


def in_scope(path, scope):
    for s in scope:
        if s in ("*", "**", "/"):
            return True
        if path == s or path.startswith(s.rstrip("/") + "/") or fnmatch.fnmatch(path, s):
            return True
    return False


def ext(path):
    name = path.rsplit("/", 1)[-1].lower()
    return name[name.rfind("."):] if "." in name else ""


def show(title, paths):
    print(f"\n{title} ({len(paths)}):")
    for p in paths[:LIST_LIMIT]:
        print(f"  {p}")
    if len(paths) > LIST_LIMIT:
        print(f"  ... and {len(paths) - LIST_LIMIT} more")


def bad_files(base, head, changes):
    """Files added or changed that are build output, too large, or binary."""
    present = [p for p, s in changes.items() if s != "D"]
    if not present:
        return []
    binary = set()
    for line in git("diff", "--numstat", "--no-renames", base, head, "--", *present).splitlines():
        added, deleted, path = line.split("\t", 2)
        if added == "-" and deleted == "-":
            binary.add(path)
    tree = {}
    for line in git("ls-tree", "-r", "-l", head, "--", *present).splitlines():
        meta, path = line.split("\t", 1)
        _mode, kind, _sha, size = meta.split()
        tree[path] = (kind, size)
    bad = []
    for p in sorted(present):
        kind, size = tree.get(p, ("blob", "-"))
        if kind != "blob":  # a submodule pointer
            continue
        why = []
        if ext(p) in FORBIDDEN:
            why.append(f"{ext(p)} file")
        if size.isdigit() and int(size) > SIZE_LIMIT:
            why.append(f"{int(size) / 1e6:.1f} MB")
        if p in binary and ext(p) not in BINARY_OK and ext(p) not in FORBIDDEN:
            why.append("binary")
        if why:
            bad.append(f"{p} ({', '.join(why)})")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--base-ref", default="main", help="the branch the PR targets")
    ap.add_argument("--body-file")
    ap.add_argument("--labels", default="")
    a = ap.parse_args()

    body = open(a.body_file, encoding="utf-8").read() if a.body_file else ""
    labels = {x.strip() for x in a.labels.split(",") if x.strip()}
    failed = False

    if a.base_ref != "main":
        failed = True
        print(f"FAIL: the PR targets '{a.base_ref}', not 'main'. Stacked PRs aren't allowed: "
              "wait for the PR below to merge, then retarget this one to main.")

    base = git("merge-base", a.base, a.head).strip()
    changes = {}
    for line in git("diff", "--name-status", "--no-renames", base, a.head).splitlines():
        status, path = line.split("\t", 1)
        changes[path] = status[0]
    own = set(git("log", "--no-merges", "--format=", "--name-only", f"{a.base}..{a.head}").split("\n")) - {""}

    print(f"Merge base {base[:10]}; {len(changes)} files changed; "
          f"{len(own)} files touched by the branch's own commits.")

    merge_only = sorted(p for p in changes if p not in own)
    if merge_only:
        failed = True
        deleted = [p for p in merge_only if changes[p] == "D"]
        print("\nFAIL: these files change only through a merge commit, never through the "
              "branch's own commits. That is what a conflict resolved to the wrong side "
              "looks like: main's version is being thrown away.")
        if deleted:
            show("Deleted by a merge", deleted)
        show("Changed only by a merge", [f"{changes[p]} {p}" for p in merge_only if changes[p] != "D"])
        print("\nFix: merge main into the branch again and keep main's side for every file "
              "above (git checkout origin/main -- <file>), or redo the merge without "
              "'ours'. Do not resolve conflicts in GitHub's web editor.")

    scope = parse_scope(body)
    if scope:
        outside = sorted(p for p in changes if not in_scope(p, scope))
        print(f"\nScope: {', '.join(scope)}")
        if outside:
            failed = True
            print("FAIL: files changed outside the PR's Scope line.")
            show("Outside scope", [f"{changes[p]} {p}" for p in outside])
            print("\nFix: drop those changes, or add the path to the Scope line if the PR "
                  "really means to change it.")
    else:
        tops = sorted({p.split("/", 1)[0] + ("/" if "/" in p else "") for p in own})
        print(f"\nNo 'Scope:' line in the PR body. Inferred scope from own commits: {', '.join(tops) or '(none)'}")
        print("Add a line like 'Scope: " + (", ".join(tops[:3]) or "my-folder/") +
              "' to the PR body to have it enforced.")

    bad = bad_files(base, a.head, changes)
    if bad and "binaries-ok" not in labels:
        failed = True
        print("\nFAIL: binaries, build output or large files are added or changed. They "
              "belong in GitHub Releases, or are fetched by a tool into a gitignored cache.")
        show("Not allowed in the repo", bad)
        print("\nFix: remove them from the branch with a new commit. If one is a reviewed "
              "exception, the 'binaries-ok' label lets it through.")
    elif bad:
        show("Binaries let through by the 'binaries-ok' label", bad)

    deletions = sorted(p for p, s in changes.items() if s == "D")
    if len(deletions) > DELETE_LIMIT and "deletions-ok" not in labels:
        failed = True
        print(f"\nFAIL: the PR deletes {len(deletions)} files (limit {DELETE_LIMIT}). "
              "If that is intended, add the 'deletions-ok' label.")
        show("Deleted", deletions)

    print("\nPR guard: " + ("FAILED" if failed else "passed"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
