#!/usr/bin/env python3
"""Syntax-check the web app: every inline <script> in app/*.html, and every
app/**/*.js file, goes through `node --check`.

Usage: python3 .github/scripts/check_web.py [app-dir]
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = re.compile(r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script>", re.S | re.I)


def check(path, label):
    r = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
    if r.returncode:
        print(f"FAIL {label}\n{r.stderr}")
        return False
    print(f"ok   {label}")
    return True


def main():
    app = Path(sys.argv[1] if len(sys.argv) > 1 else "app")
    ok = True
    count = 0
    with tempfile.TemporaryDirectory() as tmp:
        for html in sorted(app.rglob("*.html")):
            text = html.read_text(encoding="utf-8")
            for i, m in enumerate(SCRIPT.finditer(text)):
                attrs = m.group("attrs").lower()
                if "src=" in attrs or ("type=" in attrs and "javascript" not in attrs
                                       and "module" not in attrs):
                    continue
                line = text.count("\n", 0, m.start("body")) + 1
                ext = ".mjs" if "module" in attrs else ".js"
                out = Path(tmp) / f"{html.stem}-{i}{ext}"
                # Pad with blank lines so node reports the line in the HTML file.
                out.write_text("\n" * (line - 1) + m.group("body"), encoding="utf-8")
                ok &= check(out, f"{html}:{line} (inline script {i + 1})")
                count += 1
        for js in sorted(list(app.rglob("*.js")) + list(app.rglob("*.mjs"))):
            ok &= check(js, str(js))
            count += 1
    if count == 0:
        print(f"no scripts found under {app}/")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
