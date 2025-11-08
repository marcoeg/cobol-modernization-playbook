plugins {
    kotlin("jvm") version "1.9.24"
    application
}

repositories {
    mavenCentral()
}

kotlin {
    jvmToolchain(17)
}

application {
    // Main function in ModernRunner.kt
    mainClass.set("banking.ModernRunnerKt")
}

// Run from the repo root so relative paths like "data/..." resolve
tasks.named<JavaExec>("run") {
    workingDir = project.projectDir.parentFile?.parentFile  // ../.. from rewrite/kotlin
}
