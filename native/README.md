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
pipeline pair's alternatives and alpha label, the other engine's second
opinion for English, Latin and Klingon, and a note saying which engine
translated.

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
uploads nothing.

## Try it on a phone

A test APK is built by hand on GitHub, so you don't need any of the tools above.

1. Open [Actions, Native test APK](https://github.com/squirelworks/squirrelator/actions/workflows/native-test-apk.yml)
   and press **Run workflow** (leave the branch on `main`), then **Run workflow** again.
2. Wait for the run to get a green tick, about 5 to 10 minutes. Open the run.
3. Under **Artifacts** at the bottom, download `Squirrelator-test-…`. GitHub
   hands it over as a zip; unzip it to get the `.apk`. The download lasts
   14 days.
4. Copy the `.apk` to the phone (or download it there directly), tap it, and
   allow installing from that app when Android asks. It needs Android 7.0
   or newer.

The app is called **squirrelator** and installs next to any release build
(its id ends in `.debug`). The first translation takes a few seconds while
it starts Python and unpacks the language data; after that it's quick, and it
never needs the internet.

Each test APK is signed with a new throwaway key, because no key is kept for
test builds. So to install a newer test APK, uninstall the old one first.

This isn't a release: nothing goes to Releases or Play, and the upload key
isn't used.

## Google Play

The phone app is `com.squirelworks.squirrelator` on Google Play. It goes there
the same way the SquirrelGo apps do (LanguageStudentDesk `docs/PLAY.md`).

### Version

The app's version is the engine's: `version` in `pyproject.toml`, which each
release PR raises. `versionCode` follows from it (0.1.1 is 101, 1.2.3 is
10203), so it always goes up. Play shows each release as
**squirrelator 0.1.1**: the app's name and version.

### How a build gets to testers

1. The owner publishes a release (`v0.1.1`). The **Google Play** workflow
   (`.github/workflows/play.yml`) builds the AAB from that tag, signs it with
   the upload key and sends it to the **internal testing** track. The AAB is
   deleted on the runner; it's never an artifact, a release asset or a commit.
2. When internal testing looks good: **Actions → Google Play → Run workflow**,
   tag `v0.1.1`, action **promote**. That moves the same build to
   **closed testing** (Play's "Closed testing - Alpha" track). Nothing is
   built again.

The same form can **upload** a tag again by hand, or **check** the secrets
(it unlocks the key and opens Play without changing anything).

While the app has never been published, Play only takes a release as a draft.
The workflow then sends it as one and says so in the log: open Play Console →
**Test and release → Testing → Internal testing**, edit the draft release and
press **Start rollout**. After that first time, releases roll out by
themselves.

### Store listing

Everything for the listing is in `android/src/main/play/`:

| File | Play Console field |
| --- | --- |
| `icon.png` (512 × 512) | App icon |
| `feature.png` (1024 × 500) | Feature graphic |
| `screenshots/phone-*.png` (1080 × 1920) | Phone screenshots |
| `listing/en-US/title.txt` | App name |
| `listing/en-US/short-description.txt` | Short description |
| `listing/en-US/full-description.txt` | Full description |

The screenshots are the real translate screen with the engine and data from
this repo. The launcher icon in `android/src/main/res/` is the same picture.

### One-time setup (owner)

Add these **repository secrets** in this repo (**Settings → Secrets and
variables → Actions → New repository secret**). They're the same values as
LanguageStudentDesk's; GitHub can't copy secrets from one repo to another:

| Secret | Value |
| --- | --- |
| `PLAY_SERVICE_ACCOUNT_JSON` | the whole JSON key of the Play service account |
| `UPLOAD_KEYSTORE_BASE64` | the upload keystore, base64: `base64 -w0 upload.jks` (macOS: `base64 -i upload.jks`) |
| `UPLOAD_STORE_PASSWORD` | the keystore password |
| `UPLOAD_KEY_ALIAS` | the key's alias |
| `UPLOAD_KEY_PASSWORD` | the key's password |

In Play Console → **Users and permissions**, the service account needs
**Release apps to testing tracks** and **View app information** for
squirrelator. If it was given those for the whole account, that already
covers it.

Optional repository **variables**: `PLAY_TRACK` if your closed testing track
isn't the default `alpha`, and `PLAY_INTERNAL_TRACK` if internal testing
isn't `internal`.

To build a Play bundle on your own computer, put `upload.storeFile`,
`upload.storePassword`, `upload.keyAlias` and `upload.keyPassword` in
`native/local.properties` and run `gradle :android:bundleRelease`. Without
them the bundle is debug-signed, which Play refuses.
