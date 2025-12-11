@echo off
REM =============================================================================
REM SBMS Android Build Complete Fix Script
REM Fixes all gradle, dependency, SDK, and configuration issues
REM =============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo SBMS Android Build System - Complete Fix Script
echo ============================================================================
echo.

REM Check if we're in the right directory
if not exist "build.gradle.kts" (
    echo ERROR: Not in android directory. Run this from: SBMS\android\
    pause
    exit /b 1
)

echo [1/10] Stopping all Gradle daemons...
call gradlew.bat --stop >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/10] Cleaning gradle cache and builds...
if exist ".gradle" rmdir /s /q ".gradle" >nul 2>&1
if exist "build" rmdir /s /q "build" >nul 2>&1
if exist "app\build" rmdir /s /q "app\build" >nul 2>&1
timeout /t 1 /nobreak >nul

echo [3/10] Restoring files from git (remove manual edits)...
git restore . >nul 2>&1

echo [4/10] Creating gradle.properties with all necessary settings...
(
    echo # Gradle Configuration
    echo org.gradle.jvmargs=-Xmx2048m
    echo org.gradle.parallel=true
    echo org.gradle.caching=true
    echo.
    echo # AndroidX Settings
    echo android.useAndroidX=true
    echo android.enableJetifier=false
    echo android.suppressUnsupportedCompileSdk=35
    echo.
    echo # Build Settings
    echo android.enableDexingArtifactTransform=true
    echo kotlin.incremental=true
) > gradle.properties

echo [5/10] Updating app\build.gradle.kts with correct dependencies...
(
    echo plugins {
    echo     id("com.android.application")
    echo     kotlin("android")
    echo }
    echo.
    echo android {
    echo     namespace = "com.ckchdx.sbms"
    echo     compileSdk = 34
    echo.
    echo     defaultConfig {
    echo         applicationId = "com.ckcdhx.sbms"
    echo         minSdk = 21
    echo         targetSdk = 34
    echo         versionCode = 1
    echo         versionName = "1.0.0-alpha"
    echo     }
    echo.
    echo     buildTypes {
    echo         release {
    echo             isMinifyEnabled = true
    echo             proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro"^)
    echo         }
    echo     }
    echo.
    echo     compileOptions {
    echo         sourceCompatibility = JavaVersion.VERSION_17
    echo         targetCompatibility = JavaVersion.VERSION_17
    echo     }
    echo.
    echo     kotlinOptions {
    echo         jvmTarget = "17"
    echo     }
    echo }
    echo.
    echo dependencies {
    echo     implementation("androidx.core:core-ktx:1.13.1"^)
    echo     implementation("androidx.appcompat:appcompat:1.7.0"^)
    echo     implementation("com.google.android.material:material:1.12.0"^)
    echo     implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.0"^)
    echo     implementation("androidx.documentfile:documentfile:1.0.1"^)
    echo     implementation("com.jakewharton.timber:timber:5.0.1"^)
    echo     implementation("com.google.code.gson:gson:2.10.1"^)
    echo.
    echo     testImplementation("junit:junit:4.13.2"^)
    echo     androidTestImplementation("androidx.test.ext:junit:1.2.0"^)
    echo     androidTestImplementation("androidx.test.espresso:espresso-core:3.6.0"^)
    echo }
) > app\build.gradle.kts

echo [6/10] Updating build.gradle.kts ^(root^)...
(
    echo plugins {
    echo     id("com.android.application"^ version "8.2.0" apply false
    echo     kotlin("android"^ version "1.9.21" apply false
    echo }
) > build.gradle.kts

echo [7/10] Updating settings.gradle.kts...
(
    echo pluginManagement {
    echo     repositories {
    echo         google()
    echo         mavenCentral()
    echo         gradlePluginPortal()
    echo     }
    echo }
    echo.
    echo dependencyResolutionManagement {
    echo     repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS^)
    echo     repositories {
    echo         google()
    echo         mavenCentral()
    echo     }
    echo }
    echo.
    echo rootProject.name = "SBMS"
    echo include(":app"^)
) > settings.gradle.kts

echo [8/10] Downloading dependencies...
call gradlew.bat dependencies >nul 2>&1
timeout /t 3 /nobreak >nul

echo [9/10] Running clean build...
call gradlew.bat clean >nul 2>&1

echo [10/10] Building APK...
call gradlew.bat assembleDebug

echo.
echo ============================================================================

if exist "app\build\outputs\apk\debug\app-debug.apk" (
    echo SUCCESS! APK built successfully!
    echo Location: app\build\outputs\apk\debug\app-debug.apk
    echo.
    echo Next steps:
    echo 1. Connect your device
    echo 2. Run: adb install -r app\build\outputs\apk\debug\app-debug.apk
    echo 3. Launch app and grant permissions
) else (
    echo BUILD FAILED - Check errors above
)

echo ============================================================================
pause
