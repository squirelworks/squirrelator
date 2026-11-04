// The desktop build of the same screens. For now it runs the engine with the
// python3 already on the computer; bundling a Python comes with packaging.
plugins {
    kotlin("jvm")
    kotlin("plugin.compose")
    id("org.jetbrains.compose")
}

val repoRoot = rootDir.parentFile

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

kotlin {
    compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) }
}

dependencies {
    implementation(project(":ui"))
    implementation(compose.desktop.currentOs)
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-swing:1.10.2")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.8.1")
    testImplementation(kotlin("test"))
}

// Where the engine and its data live when run from a checkout.
val engineProps = mapOf(
    "squirrelator.root" to repoRoot.absolutePath,
    "squirrelator.bridge" to File(rootDir, "python/squirrelator_bridge.py").absolutePath,
    "squirrelator.data" to File(repoRoot, "data").absolutePath,
)

tasks.test {
    useJUnitPlatform()
    systemProperties(engineProps)
}

compose.desktop {
    application {
        mainClass = "com.squirelworks.squirrelator.desktop.MainKt"
        jvmArgs += engineProps.map { (k, v) -> "-D$k=$v" }
        // Installers (deb, msi, dmg) come in a later PR with a bundled Python.
    }
}
