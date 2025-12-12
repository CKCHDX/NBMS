# SBMS - Quick Start Guide

## Overview

SBMS (Samsung Bluetooth Message Service) allows a Samsung E1310E phone to send SMS messages through a paired modern Android phone (Z Fold 6) via Bluetooth.

## Requirements

### Hardware
- **Primary Device**: Samsung Z Fold 6 (Android 12+)
- **Secondary Device**: Samsung E1310E
- **Pairing**: Devices must be previously paired via Bluetooth
- **Network**: Z Fold 6 must have cellular/SMS capability

### Software

**Android (Z Fold 6)**:
- Android 12 or higher
- Bluetooth enabled
- SMS permission granted
- ~5 MB disk space

**E1310E**:
- J2ME MIDP 2.0 support
- Bluetooth 2.0 + EDR
- OPP service enabled
- ~100 KB free memory

## Installation

### Step 1: Pair Devices

**On Z Fold 6**:
1. Settings → Bluetooth → Pair new device
2. Select E1310E from nearby devices
3. Confirm pairing on both devices
4. Note the Bluetooth MAC address

**On E1310E**:
1. Menu → Settings → Bluetooth
2. Enable Bluetooth
3. Set to Discoverable
4. Search for Z Fold 6
5. Confirm pairing

### Step 2: Install Android App (Z Fold 6)

**Option A: From APK File**

```bash
# Download APK from releases
wget https://github.com/CKCHDX/SBMS/releases/download/v1.0/SBMS-android.apk

# Install via adb
adb install SBMS-android.apk

# Or transfer via USB and install via phone UI
```

**Option B: Build from Source**

```bash
git clone https://github.com/CKCHDX/SBMS.git
cd SBMS
git checkout android-apk

./gradlew assembleDebug
adb install build/outputs/apk/debug/app-debug.apk
```

### Step 3: Install E1310E App

**Option A: Via Bluetooth OPP**

```bash
# From Linux/Mac with obexftp
obexftp -b E1:31:0E:XX:XX:XX -p SBMS.jar

# Replace with actual E1310E Bluetooth MAC address
```

**Option B: Via HTTP Server**

```bash
# Host files
cp dist/SBMS.* /var/www/html/sbms/

# From E1310E, browse to:
http://YOUR_IP/sbms/SBMS.jad
```

**Option C: Build from Source**

```bash
git clone https://github.com/CKCHDX/SBMS.git
cd SBMS
git checkout E1310E-app

# Install WTK
cd /opt && tar xzf WTK2.5.2.tar.gz

# Build
ant jar

# Deploy (see options above)
```

## Configuration

### Android App

1. Launch SBMS on Z Fold 6
2. Tap "Connect to E1310E"
3. App discovers and connects automatically
4. Grant Bluetooth & SMS permissions if prompted

### E1310E App

1. Open E1310E Applications menu
2. Select SBMS
3. App loads contacts from phone (first time takes 5 seconds)
4. Contacts appear in list

## Usage

### Sending a Message from E1310E

```
1. E1310E: Open SBMS app
   ↓
2. E1310E: Search and select contact
   "Find Contact: Mom"
   ↓
3. E1310E: Type message (max 160 chars)
   "Hi Mom, how are you?"
   ↓
4. E1310E: Press "Send"
   Status: "Sending..."
   ↓
5. Z Fold 6: App receives message via Bluetooth
   Parses vCard format
   ↓
6. Z Fold 6: Sends SMS to recipient
   +46701234567 ← from vCard
   "Hi Mom, how are you?" ← from vCard
   ↓
7. Z Fold 6: Sends delivery status back via Bluetooth
   ↓
8. E1310E: Displays confirmation
   "✓ Message sent to Mom"
   Message moved to /Sent/ folder
```

### Sending a Message from Z Fold 6

1. Z Fold 6: Open SBMS app
2. Search for contact (or type phone number)
3. Type message (max 160 chars)
4. Tap "Send Message"
5. SMS sent immediately via cellular network
6. Message saved to database
7. E1310E notified of incoming SMS (if configured)

## Troubleshooting

### "Connection Failed" Error

**Problem**: Z Fold 6 can't connect to E1310E

**Solutions**:
1. Verify Bluetooth is enabled on both devices
2. Check devices are within 10 meters
3. Confirm E1310E Bluetooth MAC in Android app code
4. Restart both phones
5. Unpair and re-pair devices

### Message Not Sending

**Problem**: "Failed to send message" on E1310E

**Solutions**:
1. Check Z Fold 6 has SMS capability (cellular network active)
2. Verify contact phone number format (e.g., +46701234567)
3. Check 160 character limit
4. Ensure Bluetooth connection is active
5. Check Z Fold 6 app has SMS permission

### Contacts Not Loading

**Problem**: E1310E shows empty contact list

**Solutions**:
1. Check Z Fold 6 app has READ_CONTACTS permission
2. Ensure contacts exist on Z Fold 6
3. First load may take 5-10 seconds
4. Try restarting E1310E app
5. Sync contacts to phone if using Google Contacts

### Bluetooth Keeps Disconnecting

**Problem**: Bluetooth connection drops frequently

**Solutions**:
1. Check for interference (WiFi, microwave)
2. Move closer (within 5m)
3. Update phone firmware
4. Clear Bluetooth cache on both devices
5. Try different Bluetooth channel (technical)

## Performance

### Typical Timings

- **Bluetooth Connect**: 3-5 seconds
- **Message Send**: 1-2 seconds
- **SMS Delivery**: 2-5 seconds (network dependent)
- **Status Return**: 1-2 seconds
- **Total Round Trip**: 8-13 seconds

### Tips for Best Performance

1. **Close Other Bluetooth Devices**: Reduces interference
2. **Keep Devices In View**: Better signal
3. **Avoid Obstacles**: Water, metal, walls reduce range
4. **Check Battery**: Low battery can affect Bluetooth
5. **Use Clear Signal Area**: Away from other RF sources

## Common Workflows

### Workflow 1: Quick Text Messages

```
E1310E User:
1. Open SBMS
2. Select "Mom" from quick list
3. Type short message
4. Press Send
5. Get confirmation in ~10 seconds
```

### Workflow 2: Longer Messages

```
E1310E User:
1. Open SBMS
2. Search for contact
3. Type message (split into 160 chars if needed)
4. Send
5. For longer: Send multiple messages

Z Fold 6 User receives each as separate SMS
```

### Workflow 3: Receive SMS on E1310E

```
(Automatic process)
1. Someone texts Z Fold 6 number
2. Z Fold 6 app detects incoming SMS
3. Parses message and contact info
4. Sends via Bluetooth to E1310E
5. E1310E receives and displays (optional)

Note: Requires app to be running on both devices
```

## Permissions Required

### Z Fold 6 (Android)

- **Bluetooth**: Connect to E1310E device
- **SMS**: Send text messages via cellular
- **Contacts**: Read phone's contact list
- **Storage**: Save message history

### E1310E (J2ME)

- **Bluetooth I/O**: Connect to Z Fold 6
- **File Access**: Store messages locally

Both permissions are granted at installation.

## Advanced Configuration

### Custom E1310E MAC Address

Edit Android app's `BluetoothManager.java`:

```java
private String getE1310EMacAddress() {
    return "E1:31:0E:XX:XX:XX"; // Your E1310E's MAC
}
```

Then rebuild and install.

### Custom Contacts

Edit E1310E's `ContactManager.java`:

```java
private void loadStoredContacts() {
    storedContacts.addElement(new Contact("Name", "+46XXX"));
    // Add more contacts as needed
}
```

Then rebuild JAR and redeploy.

## Support

### Getting Help

1. **Check documentation**: README-ANDROID.md, README-E1310E.md
2. **Search issues**: https://github.com/CKCHDX/SBMS/issues
3. **Create new issue** with:
   - Device models and OS versions
   - Exact error message
   - Steps to reproduce
   - Logs if available

### Reporting Bugs

Include:
- Device: Z Fold 6 (Android 14)
- E1310E Bluetooth state
- App version
- Error message
- Screenshots if applicable

## Next Steps

- [Full Android Documentation](README-ANDROID.md)
- [Full E1310E Documentation](README-E1310E.md)
- [Technical Specification](service.md)
- [Project Structure](PROJECT_STRUCTURE.md)
- [Issue Tracker](https://github.com/CKCHDX/SBMS/issues)

## Tips & Tricks

1. **Quick Connect**: Keep both devices nearby for faster pairing
2. **Message Templates**: Create pre-written common messages
3. **Contact Shortcuts**: Put frequent contacts first in list
4. **Battery**: SBMS uses minimal power; check for other apps
5. **Privacy**: Only use with trusted, paired devices

---

**Version**: 1.0.0
**Last Updated**: December 2025
**Author**: Alex Jonsson (@CKCHDX)
