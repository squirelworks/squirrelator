import java.util.Properties

// The Android build of the shared screens. The translation engine is the
// Python package in squirrelator/ at the repo root, run inside the app by
// Chaquopy. Nothing here is a copy of it.
plugins {
    id("com.android.application")
    kotlin("android")
    kotlin("plugin.compose")
    id("com.chaquo.python")
}

val repoRoot = rootDir.parentFile
val langData = File(repoRoot, "data")

// The app's version is the engine's: pyproject.toml's version, which the
// release PR raises. versionCode follows from it (0.1.1 -> 101, 1.2.3 ->
// 10203), so it always goes up with the version, as Play needs. Each part
// stays below 100.
val appVersion: String = Regex("""(?m)^version\s*=\s*"([^"]+)"""")
    .find(File(repoRoot, "pyproject.toml").readText())!!.groupValues[1]
val appVersionCode: Int = appVersion.split(".").map { it.toInt() }.let { (major, minor, patch) ->
    require(minor < 100 && patch < 100) { "version $appVersion: minor and patch must stay below 100" }
    major * 10000 + minor * 100 + patch
}

// Play takes only bundles signed with the app's upload key. Release builds
// read it from UPLOAD_STORE_FILE, UPLOAD_STORE_PASSWORD, UPLOAD_KEY_ALIAS and
// UPLOAD_KEY_PASSWORD in the environment (the Play workflow sets these from
// secrets in LanguageStudentDesk), or upload.storeFile, upload.storePassword, upload.keyAlias and
// upload.keyPassword in the gitignored native/local.properties. Without them
// a release build is signed with the debug key, which Play refuses: fine for
// the compile check, never for an upload. Same names as the SquirrelGo apps.
val localProps = Properties().apply {
    val f = File(rootDir, "local.properties")
    if (f.isFile) f.inputStream().use { load(it) }
}
fun upload(env: String, prop: String): String? = System.getenv(env) ?: localProps.getProperty(prop)
val uploadStoreFile = upload("UPLOAD_STORE_FILE", "upload.storeFile")

android {
    namespace = "com.squirelworks.squirrelator"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.squirelworks.squirrelator"
        minSdk = 24
        targetSdk = 36
        versionCode = appVersionCode
        versionName = appVersion
        ndk {
            // Phones, plus x86_64 for the emulator.
            abiFilters += listOf("arm64-v8a", "x86_64")
        }
    }

    signingConfigs {
        if (uploadStoreFile != null) {
            create("upload") {
                storeFile = file(uploadStoreFile)
                storePassword = upload("UPLOAD_STORE_PASSWORD", "upload.storePassword")
                keyAlias = upload("UPLOAD_KEY_ALIAS", "upload.keyAlias")
                keyPassword = upload("UPLOAD_KEY_PASSWORD", "upload.keyPassword")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.findByName("upload") ?: signingConfigs.getByName("debug")
        }
        debug {
            applicationIdSuffix = ".debug"
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    sourceSets["main"].assets.srcDir(layout.buildDirectory.dir("generated/langdata"))
}

kotlin {
    compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) }
}

// Chaquopy takes whole folders, so copy just the engine package from the repo
// root (not tests, the Tk GUI, the web app or data/) into one.
val engineDir = layout.buildDirectory.dir("generated/engine")
val syncEngine by tasks.registering(Sync::class) {
    from(File(repoRoot, "squirrelator")) {
        exclude("**/__pycache__/**")
        into("squirrelator")
    }
    into(engineDir)
}

chaquopy {
    defaultConfig {
        version = "3.13"
    }
    sourceSets {
        getByName("main") {
            // The engine and the bridge the screens call. squirrelator has no
            // pip dependencies, so nothing is downloaded from PyPI.
            srcDir(engineDir)
            srcDir(File(rootDir, "python"))
        }
    }
}
tasks.matching { it.name.startsWith("merge") && it.name.endsWith("PythonSources") }
    .configureEach { dependsOn(syncEngine) }

// The language data, copied at build time from the squirrel-lang-data release
// that data/ is pinned to, so the app works offline. Only what the engine reads.
val packLangData by tasks.registering(Zip::class) {
    doFirst {
        check(File(langData, "features.json").isFile) {
            "data/ is empty. Run `git submodule update --init data` in the repo root."
        }
    }
    from(langData) {
        include("features.json", "LICENSE", "languages/**", "meaning/**")
    }
    archiveFileName.set("lang-data.zip")
    destinationDirectory.set(layout.buildDirectory.dir("generated/langdata"))
    isPreserveFileTimestamps = false
    isReproducibleFileOrder = true
}
tasks.named("preBuild") { dependsOn(packLangData) }

dependencies {
    implementation(project(":ui"))
    implementation("androidx.activity:activity-compose:1.10.1")
}
