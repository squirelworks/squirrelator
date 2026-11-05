#!/usr/bin/env python3
"""Send squirrelator's AAB to a Google Play track, or promote a release.

Used by .github/workflows/play.yml. Same script as LanguageStudentDesk's
.github/scripts/play_upload.py, plus promotion (internal testing to closed
testing without uploading again) and an automatic fall back to a draft
release while the app has never been published. The service account's JSON
key comes from the PLAY_SERVICE_ACCOUNT_JSON environment variable (a GitHub
secret); it is never written to the repo or printed.

    play_upload.py upload --package com.squirelworks.squirrelator \
        --aab android-release.aab --track internal --name "squirrelator 0.1.1" \
        --notes-file notes.txt
    play_upload.py promote --package com.squirelworks.squirrelator \
        --from-track internal --track alpha --version-code 101
    play_upload.py check com.squirelworks.squirrelator
"""
import argparse
import json
import os
import sys

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPE = "https://www.googleapis.com/auth/androidpublisher"
DOC = "see native/README.md, \"Google Play\""


def connect():
    raw = os.environ.get("PLAY_SERVICE_ACCOUNT_JSON", "")
    if not raw.strip():
        sys.exit(f"PLAY_SERVICE_ACCOUNT_JSON is not set; {DOC}")
    creds = service_account.Credentials.from_service_account_info(json.loads(raw), scopes=[SCOPE])
    return build("androidpublisher", "v3", credentials=creds, cache_discovery=False)


def explain(pkg, e):
    """Play's refusal, with what to do about it."""
    msg = e.reason or str(e)
    low = msg.lower()
    hint = ""
    if "apk signature" in low or "wrong key" in low or "upload key" in low or "debug" in low:
        hint = " (the AAB isn't signed with this app's registered upload key)"
    elif "package not found" in low or e.resp.status == 404:
        hint = " (the app isn't in Play Console, or the service account has no access to it)"
    elif "draft app" in low:
        hint = " (the app has never been published; send it as a draft)"
    elif "versioncode" in low or "version code" in low:
        hint = " (that versionCode is already on Play; raise the version in pyproject.toml)"
    return f"{pkg}: Play refused: {msg}{hint}; {DOC}"


def is_draft_app(e):
    return "draft app" in (e.reason or str(e)).lower()


def check(packages):
    """Open and discard an edit for each package: proves access, changes nothing."""
    api = connect()
    bad = 0
    for pkg in packages:
        try:
            eid = api.edits().insert(packageName=pkg, body={}).execute()["id"]
            tracks = api.edits().tracks().list(packageName=pkg, editId=eid).execute().get("tracks", [])
            api.edits().delete(packageName=pkg, editId=eid).execute()
            print(f"OK   {pkg}  tracks: {', '.join(t['track'] for t in tracks)}")
        except HttpError as e:
            bad += 1
            print(f"FAIL {explain(pkg, e)}")
    if bad:
        sys.exit(f"{bad} app(s) not reachable")


def commit_release(edits, pkg, eid, track, release, status):
    """Put the release on the track and commit. 'auto' is completed, or a
    draft when Play says the app has never been published."""
    for attempt in (["completed", "draft"] if status == "auto" else [status]):
        release["status"] = attempt
        try:
            edits.tracks().update(packageName=pkg, editId=eid, track=track,
                                  body={"track": track, "releases": [release]}).execute()
            edits.commit(packageName=pkg, editId=eid).execute()
            return attempt
        except HttpError as e:
            if attempt == "completed" and status == "auto" and is_draft_app(e):
                print("::warning::Play says the app has never been published, so this release is a "
                      "draft. Roll it out once in Play Console (" + DOC + ").")
                continue
            raise


def upload(a):
    api = connect()
    edits = api.edits()
    try:
        eid = edits.insert(packageName=a.package, body={}).execute()["id"]
        media = MediaFileUpload(a.aab, mimetype="application/octet-stream", resumable=True)
        code = edits.bundles().upload(packageName=a.package, editId=eid, media_body=media).execute()["versionCode"]
        release = {"name": a.name, "versionCodes": [str(code)]}
        if a.notes_file and os.path.exists(a.notes_file):
            text = open(a.notes_file, encoding="utf-8").read().strip()[:500]
            if text:
                release["releaseNotes"] = [{"language": "en-US", "text": text}]
        status = commit_release(edits, a.package, eid, a.track, release, a.status)
    except HttpError as e:
        sys.exit(explain(a.package, e))
    print(f"{a.package}: versionCode {code} ('{a.name}') sent to the '{a.track}' track as {status}")


def promote(a):
    """Copy the release holding --version-code from one track to another.
    Nothing is uploaded: Play reuses the bundle it already has."""
    api = connect()
    edits = api.edits()
    code = str(a.version_code)
    try:
        eid = edits.insert(packageName=a.package, body={}).execute()["id"]
        src = edits.tracks().get(packageName=a.package, editId=eid, track=a.from_track).execute()
        found = [r for r in src.get("releases", []) if code in r.get("versionCodes", [])]
        if not found:
            edits.delete(packageName=a.package, editId=eid).execute()
            have = sorted({c for r in src.get("releases", []) for c in r.get("versionCodes", [])})
            sys.exit(f"{a.package}: versionCode {code} isn't on the '{a.from_track}' track "
                     f"(it has: {', '.join(have) or 'nothing'}). Upload it there first.")
        old = found[0]
        release = {"name": old.get("name", ""), "versionCodes": [code]}
        if old.get("releaseNotes"):
            release["releaseNotes"] = old["releaseNotes"]
        status = commit_release(edits, a.package, eid, a.track, release, a.status)
    except HttpError as e:
        sys.exit(explain(a.package, e))
    print(f"{a.package}: versionCode {code} ('{release['name']}') promoted from "
          f"'{a.from_track}' to '{a.track}' as {status}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="prove the service account can reach each package")
    c.add_argument("packages", nargs="+")

    status = dict(default="auto", choices=["auto", "completed", "draft"],
                  help="'completed' rolls out to the track's testers; 'draft' waits in Play Console; "
                       "'auto' is completed, or draft while the app has never been published")
    u = sub.add_parser("upload", help="upload an AAB and release it on a track")
    u.add_argument("--package", required=True)
    u.add_argument("--aab", required=True)
    u.add_argument("--track", default="internal")
    u.add_argument("--status", **status)
    u.add_argument("--name", required=True, help="release name shown in Play Console")
    u.add_argument("--notes-file", help="plain text 'What's new' (en-US), at most 500 characters")

    p = sub.add_parser("promote", help="copy a release from one track to another")
    p.add_argument("--package", required=True)
    p.add_argument("--from-track", default="internal")
    p.add_argument("--track", default="alpha", help="'alpha' is Play's default closed testing track")
    p.add_argument("--version-code", required=True, type=int)
    p.add_argument("--status", **status)

    a = ap.parse_args()
    {"check": lambda: check(a.packages), "upload": lambda: upload(a), "promote": lambda: promote(a)}[a.cmd]()


if __name__ == "__main__":
    main()
