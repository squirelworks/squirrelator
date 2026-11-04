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

android {
    namespace = "com.squirelworks.squirrelator"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.squirelworks.squirrelator"
        minSdk = 24
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"
        ndk {
            // Phones, plus x86_64 for the emulator.
            abiFilters += listOf("arm64-v8a", "x86_64")
        }
    }

    buildTypes {
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
