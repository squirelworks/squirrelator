// One Gradle project, two builds of the same screens: the Android app and the
// desktop app. See native/README.md.
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "squirrelator-native"
include(":ui", ":android", ":desktop")
