# squirrelator native apps

The phone app and the desktop app, built from one set of screens. Same plan
as LanguageStudentDesk's
[decision 0001](https://github.com/squirelworks/LanguageStudentDesk/blob/main/docs/decisions/0001-native-apps.md):
Kotlin with Compose Multiplatform, where Android and desktop are two builds of
the same code. See issue #25.

```
native/
  ui/        the screens, written once (Kotlin, commonMain)
  android/   the Android app: the screens plus the Python engine via Chaquopy
  desktop/   the desktop app: the screens plus the Python engine in a python3 process
  python/    squirrelator_bridge.py, the one thing both apps call
```

## One engine

The translation engine stays the Python package in `squirrelator/` at the repo
root. Nothing here copies or rewrites it.

- **Android** runs it inside the app with [Chaquopy](https://chaquo.com/chaquopy/).
  The build copies `squirrelator/` and `python/squirrelator_bridge.py` into the
  app. The engine has no pip dependencies, so nothing comes from PyPI.
- **Desktop** starts `python3 python/squirrelator_bridge.py --serve` and sends it
  one JSON line per request. For now that's the `python3` on the computer;
  installers that carry their own Python come later.

The screens show what the desktop GUI shows under its Auto engine
(`squirrelator.menus.display`): `translate()`'s default routing, with a
pipeline pair's alternatives and alpha label, the second opinion for Latin
and Klingon, and a note saying which engine translated.

## Language data

The Android build packs `features.json`, `LICENSE`, `languages/` and `meaning/`
from `data/` (the pinned squirrel-lang-data release) into the app, so it works
offline. `tests/test_native_bridge.py` checks the engine gives the same answers
from that part as from the whole checkout. The desktop app reads `data/`
directly.

## Building

You need JDK 17 or newer, Gradle 8.14, Python 3.10 or newer and, for Android,
the Android SDK with platform 36. From the repo root:

```
git submodule update --init data
cd native
gradle :ui:desktopTest :desktop:test   # tests
gradle :desktop:run                    # the desktop app
gradle :android:assembleDebug          # a debug APK in android/build/outputs/apk/debug/
```

For Android, put `sdk.dir=/path/to/Android/sdk` in `native/local.properties`
or set `ANDROID_HOME`.

CI (`.github/workflows/native.yml`) runs the same commands on every PR and
uploads nothing. Release signing (APKs signed in GitHub Actions with the upload
key from GitHub secrets, AABs never on GitHub) comes with the first release.
