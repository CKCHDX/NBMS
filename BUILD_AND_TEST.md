# SBMS Build & Test Guide

## Quick Build Instructions

### Prerequisites

```bash
# Check Java version (need 17+)
java -version

# Check Android SDK
# Android Studio → Settings → SDK Manager
# Ensure API 35 (Android 15) installed
```

### Clone & Build

```bash
# Clone the repository
git clone https://github.com/CKCHDX/SBMS.git
cd SBMS

# Switch to android-phase3 branch
git checkout android-phase3

# Navigate to Android project
cd android

# Build debug APK
./gradlew assembleDebug

# Or directly install to connected device
./gradlew installDebug
```

**Expected Output**:
```
...
Build successful
APK: android/app/build/outputs/apk/debug/app-debug.apk
```

---

## Installation on Z Fold 6

### Method 1: Android Studio (Easiest)

1. Open Android Studio
2. File → Open → SBMS/android
3. Ensure Z Fold 6 is connected (USB debugging enabled)
4. Click ▶️ **Run** button
5. Select "Z Fold 6" as target device
6. App installs and launches automatically

### Method 2: ADB Command Line

```bash
# List connected devices
adb devices

# Install debug APK
adb install android/app/build/outputs/apk/debug/app-debug.apk

# Launch app
adb shell am start -n com.ckchdx.sbms/.MainActivity

# View logs in real-time
adb logcat -s SBMSBluetoothService:* SBMSMainActivity:* SMSManager:*
```

### Method 3: Manual APK Transfer

```bash
# Copy APK to device via USB
adb push android/app/build/outputs/apk/debug/app-debug.apk /sdcard/Download/

# On device: Open Files → Download → app-debug.apk → Install
```

---

## Permissions Grant

When app first starts, grant these permissions:

1. **Bluetooth**
   - ✅ Nearby devices
   - ✅ Bluetooth

2. **SMS**
   - ✅ Send and view SMS messages
   - ✅ Read SMS messages

3. **Files**
   - ✅ Photos and videos
   - ✅ Access all files

4. **Contacts**
   - ✅ Read contacts

All should show **green checkmark** (✅)

---

## Testing Phase 1: Manual Bluetooth Transfer

### Goal
Verify Bluetooth OPP file transfer works in both directions

### Setup

1. **Pair Devices**
   ```
   Z Fold 6: Settings → Bluetooth
              Search for E1310E
              Tap "Pair"
   
   E1310E: Menu → Settings → Bluetooth
           Accept pairing request
   ```

2. **Confirm Pairing**
   ```
   Both devices should show:
   "Connected" or "Paired" status
   ```

### Test 1A: E1310E → Z Fold 6

```
E1310E Menu:
  → Contacts
  → Select any contact
  → Options (or soft key)
  → "Send via Bluetooth"
  → Select Z Fold 6
  → Confirm send
  
 Expected: File transfer ~1-3 seconds
```

**Find the file on Z Fold 6**:
```bash
adb shell find /sdcard -name "*.vcd" -o -name "*.vcf" 2>/dev/null

# Typical locations:
/sdcard/Download/Bluetooth/
/sdcard/Bluetooth/
/sdcard/Download/
```

**Check file content**:
```bash
adb shell cat /sdcard/Download/Bluetooth/<filename>

# Should contain:
BEGIN:VCARD
VERSION:2.1
FN:<Contact Name>
TEL:<Phone Number>
END:VCARD
```

**Record the file path** - You'll need this for SBMS configuration if different from `/sdcard/Download/Bluetooth/`

### Test 1B: Z Fold 6 → E1310E (Reverse Transfer)

```bash
# Create test vCard on Z Fold 6
adb shell cat > /sdcard/test.vcf << 'EOF'
BEGIN:VCARD
VERSION:2.1
FN:Test Contact
TEL:+46701234567
END:VCARD
EOF
```

**Send from Z Fold 6**:
```
Z Fold 6: Files → /sdcard/test.vcf
           Long press → "Share"
               → "Bluetooth"
               → Select E1310E
               → Confirm
```

**Check on E1310E**:
```
E1310E: Menu → Bluetooth Services
        Should see new contact or file
```

### Results

Fill in these metrics:

```
Test Date: ________
Z Fold 6 Model: ________
E1310E Model: ________
Android Version: ________
Bluetooth Signal: Strong / Good / Fair / Weak

E1310E → Z Fold 6:
  - File detected: Yes / No
  - File location: ____________________________
  - Transfer time: _____ seconds
  - Success rate: _____ / 5 attempts

Z Fold 6 → E1310E:
  - File received: Yes / No
  - E1310E recognized file: Yes / No
  - Transfer time: _____ seconds
  - Success rate: _____ / 5 attempts
```

---

## Testing Phase 3.1: SBMS App Reception

### Goal
Verify Android app detects, parses, and processes Bluetooth messages

### Setup

1. **Install and start SBMS app**
   ```bash
   ./gradlew installDebug
   # App opens automatically
   ```

2. **Grant permissions** (if not already done)
   - Tap each permission request
   - Select "Allow"

3. **Start service**
   - Tap "Start Service" button
   - Verify status shows ✓ "Running"

### Test 3.1A: Manual vCard Transfer

```bash
# Create test vCard with SBMS properties
adb shell cat > /sdcard/sbms_test.vcd << 'EOF'
BEGIN:VCARD
VERSION:2.1
PRODID:-//SBMS//1.0//EN
X-SBMS-MSG:true
X-SBMS-TYPE:1
X-SBMS-TO:+46123456789
X-SBMS-TEXT:Test message from SBMS
X-SBMS-PRIORITY:1
X-SBMS-TIMESTAMP:20251211T150700Z
X-SBMS-UUID:ABCD1234
END:VCARD
EOF
```

**Transfer to Bluetooth folder**:
```bash
# Copy to Bluetooth folder (discovered in Phase 1)
adb shell cp /sdcard/sbms_test.vcd \
    /sdcard/Download/Bluetooth/sbms_test.vcd

# Alternative: Use "Share via Bluetooth" from Files app
```

**Check app logs**:
```bash
# Real-time log monitoring
adb logcat -s SBMS* | grep -E "(Processing|Received|Parsing|Valid|Sending)"

# Expected output:
SBMSBluetoothService: Processing vCard: sbms_test.vcd
SBMSBluetoothService: Received SBMS message: TO=+46123456789, TEXT=Test message...
SBMSBluetoothService: SBMS message processed - Status: SENT
```

### Test 3.1B: Multiple Rapid Messages

```bash
# Create 5 test messages
for i in {1..5}; do
  cat > /sdcard/sbms_test_$i.vcd << EOF
BEGIN:VCARD
VERSION:2.1
X-SBMS-TO:+46123456789
X-SBMS-TEXT:Message $i
X-SBMS-UUID:UUID00$i
END:VCARD
EOF
done

# Copy all to Bluetooth folder
for i in {1..5}; do
  adb shell cp /sdcard/sbms_test_$i.vcd \
      /sdcard/Download/Bluetooth/sbms_test_$i.vcd
done
```

**Check app response**:
- Should process all 5 messages
- Each should appear in logcat
- All files should be deleted after processing

### Test 3.1C: Invalid Message Handling

```bash
# Create invalid vCard (missing phone number)
adb shell cat > /sdcard/sbms_invalid.vcd << 'EOF'
BEGIN:VCARD
VERSION:2.1
X-SBMS-TEXT:No phone number
X-SBMS-UUID:INVALID01
END:VCARD
EOF

adb shell cp /sdcard/sbms_invalid.vcd \
    /sdcard/Download/Bluetooth/sbms_invalid.vcd
```

**Check logs**:
```bash
adb logcat -s SBMS* | grep -i "invalid\|failed\|error"

# Expected:
SBMSBluetoothService: Invalid message: ...
SBMSBluetoothService: Deleted processed file: sbms_invalid.vcd
```

### Test Results

```
Test Date: ________

Test 3.1A (Single Valid Message):
  - Message detected: Yes / No
  - Parsing successful: Yes / No
  - Phone number validation: Passed / Failed
  - SMS queued: Yes / No
  - Logcat shows success: Yes / No

Test 3.1B (Multiple Rapid Messages):
  - All 5 detected: Yes / No
  - All parsed correctly: Yes / No
  - Processing order correct: Yes / No
  - All files deleted: Yes / No

Test 3.1C (Invalid Message):
  - Invalid detected: Yes / No
  - Error logged: Yes / No
  - File deleted: Yes / No
  - App didn't crash: Yes / No

Overall Success Rate: _____ %
```

---

## Debugging Tips

### Enable Verbose Logging

```bash
# All SBMS logs with timestamps
adb logcat -s SBMS* -v threadtime

# Specific component
adb logcat -s SBMSBluetoothService:V

# Filter by log level
adb logcat -s SBMS*:E  # Errors only
adb logcat -s SBMS*:W  # Warnings and errors
```

### Save Logs to File

```bash
# Continuous logging
adb logcat -s SBMS* > sbms_debug.log

# Or use Logcat in Android Studio
# View → Tool Windows → Logcat
```

### Check Bluetooth Folder Access

```bash
# List Bluetooth folder contents
adb shell ls -la /sdcard/Download/Bluetooth/

# Or other paths
adb shell ls -la /sdcard/Bluetooth/
adb shell ls -la /sdcard/Download/

# Find ALL .vcd files
adb shell find /sdcard -name "*.vcd" -o -name "*.vcf"
```

### Reset App State

```bash
# Clear app cache
adb shell pm clear com.ckchdx.sbms

# Uninstall and reinstall
adb uninstall com.ckchdx.sbms
./gradlew installDebug
```

### Check SMS Permissions

```bash
# List all permissions granted to app
adb shell dumpsys package com.ckchdx.sbms | grep -A 20 'grantedPermissions'

# Manually grant missing permission
adb shell pm grant com.ckchdx.sbms android.permission.SEND_SMS
```

---

## Common Issues & Solutions

### Issue: "No such file or directory" when building

**Cause**: Missing Android SDK

**Solution**:
```bash
# Check SDK path
echo $ANDROID_SDK_ROOT

# Or set it
export ANDROID_SDK_ROOT=~/Android/Sdk

# Install missing components
sdkmanager "platforms;android-35"
sdkmanager "build-tools;35.0.0"
```

### Issue: App doesn't detect Bluetooth files

**Cause**: Wrong folder path

**Solution**:
1. Run Phase 1 test to find correct path
2. Update `BLUETOOTH_OPP_PATHS` in `SBMSBluetoothService.kt`
3. Rebuild and test

### Issue: SMS not sending

**Cause**: Missing SEND_SMS permission or no SIM card

**Solution**:
```bash
# Grant permission manually
adb shell pm grant com.ckchdx.sbms android.permission.SEND_SMS

# Verify SIM in phone Settings
# Test manual SMS from Messages app first
```

### Issue: "Permission denied" errors

**Cause**: Scoped storage on Android 11+

**Solution**:
- Grant MANAGE_EXTERNAL_STORAGE in app settings
- Or run on device with less restrictive storage

---

## Performance Baseline

Once tests pass, measure these metrics:

```bash
# Measure file detection latency
# Send file, note time in logcat
# Should be < 4 seconds

# Measure parsing speed
# Check timestamp difference in logs
# Should be < 500ms

# Battery impact
# Use Settings → Battery → App Usage
# Compare before/after SBMS use
```

---

## Reporting Results

Once testing complete, please report:

1. **Phase 1 Results**
   - Correct Bluetooth folder path
   - Transfer success rates
   - Any version-specific issues

2. **Phase 3.1 Results**
   - App installs without errors
   - File detection works
   - Parsing succeeds for valid messages
   - Invalid messages handled gracefully

3. **Issues Encountered**
   - Any unexpected behaviors
   - Logs of failures
   - Device-specific quirks

4. **Next Steps**
   - Ready for Phase 3.2 (OPP push)?
   - Any blockers?
   - Feature requests?

---

## Contact for Support

- **GitHub Issues**: [CKCHDX/SBMS/issues](https://github.com/CKCHDX/SBMS/issues)
- **Logcat**: Capture with `adb logcat` for troubleshooting
- **Device Info**: Include Android version, device model, Bluetooth version

---

**Last Updated**: December 11, 2025
**Version**: 1.0
