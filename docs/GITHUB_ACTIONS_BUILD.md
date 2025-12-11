# Building SBMS APK with GitHub Actions (No Android Studio Required!)

## Overview

You can build the SBMS APK **directly on GitHub** without installing Android Studio or any development tools locally. GitHub Actions automatically compiles the APK whenever you push code.

---

## How It Works

### Automatic Build Triggers

The APK builds automatically when:

1. **You push to `android-phase3` or `main` branch**
   - Any commit with changes to `android/**` folder
   - Changes to the workflow file itself

2. **You create a Pull Request**
   - Builds APK for testing before merging
   - Comments on PR with download link

3. **You manually trigger it**
   - Go to Actions tab → "Android Build APK" → "Run workflow"

---

## Download APK (2 Methods)

### Method 1: From Actions Tab (Recommended)

**Step-by-Step**:

1. Go to your repository: [github.com/CKCHDX/SBMS](https://github.com/CKCHDX/SBMS)

2. Click **"Actions"** tab at the top

3. Select the latest **"Android Build APK"** workflow run
   - Green checkmark ✓ = Success
   - Red X ✗ = Failed (check logs)

4. Scroll down to **"Artifacts"** section

5. Download **"sbms-debug-apk"**
   - File: `sbms-debug-apk.zip`
   - Contains: `app-debug.apk`

6. Unzip and install:
   ```bash
   unzip sbms-debug-apk.zip
   adb install app-debug.apk
   ```

### Method 2: From Release Page (Future)

Once v1.0 is released, you'll find APKs at:
```
https://github.com/CKCHDX/SBMS/releases
```

---

## Manual Trigger (No Code Push Required)

You can build the APK **without pushing any code**:

**Steps**:

1. Go to repository → **Actions** tab

2. Select **"Android Build APK"** workflow (left sidebar)

3. Click **"Run workflow"** button (top right)

4. Select branch:
   - `android-phase3` (for latest development)
   - `main` (for stable)

5. Click green **"Run workflow"** button

6. Wait 3-5 minutes for build to complete

7. Download from Artifacts section

---

## What Gets Built

### Debug APK
- **Filename**: `app-debug.apk`
- **Size**: ~5-10 MB
- **Signing**: Debug keystore (auto-signed)
- **Use Case**: Testing and development
- **Installable**: Yes (requires "Install from unknown sources")

### Release APK (Future)
- **Filename**: `app-release-unsigned.apk`
- **Size**: ~3-5 MB (minified with ProGuard)
- **Signing**: Unsigned (needs signing for Play Store)
- **Use Case**: Production distribution

---

## Installation on Z Fold 6

### Prerequisites

1. **Enable USB Debugging**
   ```
   Settings → About Phone → Build Number (tap 7 times)
   Settings → Developer Options → USB Debugging (ON)
   ```

2. **Install ADB** (if not already)
   ```bash
   # Windows
   winget install Google.PlatformTools
   
   # macOS
   brew install android-platform-tools
   
   # Linux
   sudo apt install adb
   ```

### Install APK via ADB

```bash
# Connect Z Fold 6 via USB
adb devices
# Should show: List of devices attached
#              <device-id>    device

# Install APK
adb install -r app-debug.apk
# -r flag: Reinstall if already exists

# Launch app
adb shell am start -n com.ckchdx.sbms/.MainActivity

# View logs
adb logcat -s SBMS*
```

### Install APK via File Transfer

```bash
# Copy APK to phone
adb push app-debug.apk /sdcard/Download/

# Or use USB file transfer (MTP mode)
# Drag-and-drop app-debug.apk to Download folder
```

**On Phone**:
```
1. Open Files app
2. Navigate to Download folder
3. Tap app-debug.apk
4. Tap "Install"
5. (May need to enable "Install unknown apps" for Files)
```

---

## Troubleshooting GitHub Actions

### Build Fails

**Check the logs**:
1. Actions tab → Failed workflow
2. Click on the run
3. Click "Build SBMS APK" job
4. Expand failed step
5. Read error message

**Common Issues**:

| Error | Cause | Solution |
|-------|-------|----------|
| "Gradle build failed" | Syntax error in code | Check commit diff, fix code |
| "Could not find com.android..." | Missing dependency | Update `build.gradle.kts` |
| "Permission denied" | Gradlew not executable | Workflow already handles this |
| "Java version mismatch" | Wrong JDK | Workflow uses JDK 17 (correct) |

### No Artifacts Available

**Possible Reasons**:
- Build failed before APK creation
- Artifact expired (30-day retention)
- Workflow didn't run (no code changes in `android/`)

**Solution**:
- Manually trigger workflow (see above)
- Check workflow logs for errors
- Ensure you're on correct branch

### Can't Download Artifact

**Requirements**:
- You must be logged into GitHub
- Must have repo access (owner/collaborator)
- Artifact must not be expired

**Alternative**:
- Build locally instead (see below)

---

## Local Build (Fallback Option)

If GitHub Actions fails, you can still build locally **without Android Studio**:

### Install Prerequisites

```bash
# Install JDK 17
# Windows: winget install EclipseAdoptium.Temurin.17.JDK
# macOS: brew install openjdk@17
# Linux: sudo apt install openjdk-17-jdk

# Install Android SDK command-line tools
# Download from: https://developer.android.com/studio#command-tools
# Extract to ~/Android/cmdline-tools/

# Set environment variables
export ANDROID_HOME=~/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools

# Install SDK components
sdkmanager "platforms;android-35"
sdkmanager "build-tools;35.0.0"
```

### Build APK

```bash
# Clone repo
git clone https://github.com/CKCHDX/SBMS.git
cd SBMS && git checkout android-phase3

# Build
cd android
chmod +x gradlew  # Make gradlew executable
./gradlew assembleDebug

# APK location
# android/app/build/outputs/apk/debug/app-debug.apk
```

---

## Workflow Configuration

### Current Settings

- **Trigger**: Push to `android-phase3` or `main`, PR, manual
- **Runner**: Ubuntu Latest (GitHub-hosted)
- **JDK**: Temurin 17
- **Gradle Cache**: Enabled (faster builds)
- **Artifacts**: Debug APK (30 days retention)
- **Build Time**: ~3-5 minutes

### Modify Workflow

Edit `.github/workflows/android-build.yml`:

```yaml
# Example: Add more branches
on:
  push:
    branches:
      - android-phase3
      - main
      - feature/*  # Add this

# Example: Change retention
- name: Upload Debug APK
  uses: actions/upload-artifact@v4
  with:
    retention-days: 90  # Change from 30 to 90
```

---

## APK Signing (For Production)

### Debug vs. Release

**Debug APK** (current):
- Signed with debug keystore
- Can't publish to Play Store
- Good for testing

**Release APK** (future):
- Needs production keystore
- Required for Play Store
- Enables ProGuard minification

### Setup Release Signing

1. **Generate keystore**:
   ```bash
   keytool -genkey -v -keystore sbms-release.keystore \
     -alias sbms -keyalg RSA -keysize 2048 -validity 10000
   ```

2. **Add secrets to GitHub**:
   - Settings → Secrets → Actions
   - Add: `KEYSTORE_FILE` (base64 encoded keystore)
   - Add: `KEYSTORE_PASSWORD`
   - Add: `KEY_ALIAS`
   - Add: `KEY_PASSWORD`

3. **Update workflow** to use secrets for signing

---

## Comparison: GitHub Actions vs. Local Build

| Aspect | GitHub Actions | Local Build |
|--------|---------------|-------------|
| **Setup Time** | 0 minutes (pre-configured) | 30-60 minutes (install tools) |
| **Build Time** | 3-5 minutes | 2-4 minutes |
| **Storage** | 0 GB local (runs on GitHub) | ~5 GB (Android SDK + cache) |
| **Consistency** | Same environment every time | Depends on local setup |
| **Cost** | Free (2000 min/month) | Free |
| **Access** | Anywhere with internet | Only on dev machine |
| **Best For** | Quick testing, CI/CD | Heavy development |

**Recommendation**: Use **GitHub Actions** for building, only setup local if you need rapid iteration.

---

## Next Steps

1. **Push code** to `android-phase3` branch
2. **Check Actions tab** for build progress
3. **Download APK** from Artifacts
4. **Install on Z Fold 6**
5. **Test** Phase 3.1 functionality

---

## GitHub Actions Badge (Optional)

Add build status badge to README:

```markdown
![Android Build](https://github.com/CKCHDX/SBMS/actions/workflows/android-build.yml/badge.svg)
```

Shows: ![Build Passing](https://img.shields.io/badge/build-passing-brightgreen) or ![Build Failing](https://img.shields.io/badge/build-failing-red)

---

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Android Gradle Plugin](https://developer.android.com/build)
- [Signing Your Applications](https://developer.android.com/studio/publish/app-signing)

---

**Summary**: GitHub Actions builds your APK automatically - no Android Studio needed! Just push code and download the APK from the Actions tab. 🚀
