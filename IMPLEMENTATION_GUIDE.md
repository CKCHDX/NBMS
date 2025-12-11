# SBMS Implementation Guide

## Overview

This document guides the complete implementation of Samsung Bluetooth Message Service (SBMS) across three platforms:

1. **Android App (Samsung Galaxy Z Fold 6)** - Phase 3 (In Progress)
2. **J2ME App (Samsung E1310E)** - Phase 2 (Pending)
3. **Supporting Libraries** - Utilities and helpers

---

## Current Status: Android Implementation (Phase 3)

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Samsung Galaxy Z Fold 6 (Android 16)                        │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  MainActivity                                          │  │
│  │  - UI Status Display                                   │  │
│  │  - Permissions Management                              │  │
│  │  - Service Control                                     │  │
│  └────────────────────────────────────────────────────────┘  │
│            ↓                                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  SBMSBluetoothService (Foreground Service)             │  │
│  │  - Monitors /sdcard/Download/Bluetooth/                │  │
│  │  - Polls every 2 seconds for new .vcd files            │  │
│  │  - Parses vCard X-SBMS-* properties                    │  │
│  │  - Validates message format                            │  │
│  └────────────────────────────────────────────────────────┘  │
│            ↓                                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  SMSManager                                            │  │
│  │  - Android SmsManager API wrapper                      │  │
│  │  - Phone number normalization                          │  │
│  │  - Single/Multi-part message handling                  │  │
│  └────────────────────────────────────────────────────────┘  │
│            ↓                                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Native Android SMS API                                │  │
│  │  - Sends actual SMS via cellular network               │  │
│  │  - Captures delivery receipts                          │  │
│  └────────────────────────────────────────────────────────┘  │
│            ↓                                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Bluetooth OPP (Return Path)                           │  │
│  │  - Receives SMS status response                        │  │
│  │  - Pushes back to E1310E (Phase 3.2)                   │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

### Completed Components

✅ **Build Configuration**
- `android/app/build.gradle.kts` - Kotlin DSL with all dependencies
- Android SDK 35 (Android 16), minSdk 21
- Coroutines, AndroidX, Material Design

✅ **Android Manifest**
- Bluetooth permissions (SCAN, CONNECT, ADMIN)
- SMS permissions (SEND, RECEIVE, READ)
- File system permissions (READ/WRITE EXTERNAL STORAGE)
- Service and Receiver declarations

✅ **Core Models**
- `SBMSMessage.kt` - Data class with vCard serialization/deserialization
- Supports both text-based (vCard) and future binary formats
- Deterministic UUID handling
- ISO 8601 timestamp parsing/formatting

✅ **Service Implementation**
- `SBMSBluetoothService.kt` - Foreground service that:
  - Scans multiple Bluetooth OPP folder paths
  - Polls every 2 seconds for new .vcd files
  - Parses X-SBMS-* vCard properties
  - Validates phone numbers (E.164 + local Swedish format)
  - Validates message content
  - Sends SMS via SMSManager

✅ **Utilities**
- `SMSManager.kt` - Android SMS API wrapper that:
  - Sends single and multi-part SMS
  - Normalizes phone numbers (Swedish +46 format)
  - Handles delivery receipts
  - PendingIntent creation for callbacks

✅ **UI Layer**
- `MainActivity.kt` - Main activity with:
  - Permission request handling
  - Service start/stop controls
  - Status display
  - Bluetooth settings shortcut

✅ **Broadcast Receivers**
- `BluetoothFileReceiver.kt` - Listens for Bluetooth file arrival events

### Pending Components

❌ **Phase 3.2: OPP Response Push**
- Bluetooth OPP client implementation
- Status response generation
- Push response back to E1310E
- Retry logic for failed pushes

❌ **Phase 3.3: Delivery Receipt Integration**
- SMSDeliveryReceiver implementation
- Capture SMS delivery status
- Update response with delivery confirmation

❌ **Phase 4: Integration Testing**
- End-to-end message flow testing
- Multiple rapid message handling
- Connection failure recovery
- Battery and performance profiling

---

## Environment Setup

### Android Development

**Required:**
- Android Studio 2024.1+
- Android SDK 35
- JDK 17+
- Kotlin 1.9+

**Installation:**

```bash
# Clone repository
git clone https://github.com/CKCHDX/SBMS.git
cd SBMS

# Checkout android-phase3 branch
git checkout android-phase3

# Open in Android Studio
# File → Open → SBMS/android

# Build APK
./gradlew build

# Install to device
./gradlew installDebug
```

### Testing on Z Fold 6

1. **Enable Developer Options**
   - Settings → About Phone → Build Number (tap 7 times)
   - Settings → System → Developer Options → USB Debugging (ON)

2. **Connect via ADB**
   ```bash
   adb devices
   adb logcat -s SBMSBluetoothService:* SBMSMainActivity:* SMSManager:*
   ```

3. **Install APK**
   ```bash
   adb install android/app/build/outputs/apk/debug/app-debug.apk
   ```

---

## vCard Message Format

### Example Message from E1310E → Z Fold 6

```
BEGIN:VCARD
VERSION:2.1
PRODID:-//SBMS//1.0//EN
X-SBMS-MSG:true
X-SBMS-TYPE:1
X-SBMS-TO:+46701234567
X-SBMS-TEXT:Hej från E1310E
X-SBMS-PRIORITY:1
X-SBMS-TIMESTAMP:20251211T150700Z
X-SBMS-UUID:A3F7E2C1
END:VCARD
```

### Parsing Flow

1. **File Detection**: `.vcd` file appears in `/sdcard/Download/Bluetooth/`
2. **Content Read**: Service reads file as UTF-8 text
3. **vCard Parsing**: Line-by-line extraction of X-SBMS-* fields
4. **Model Creation**: `SBMSMessage.fromVCard()` creates object
5. **Validation**: Phone number, text length, UUID format checked
6. **SMS Send**: `SMSManager.sendSMS()` queues message
7. **Response**: Generate response with status field
8. **Cleanup**: Delete processed .vcd file

---

## Phone Number Normalization

The SMS manager handles multiple formats:

```kotlin
"+46701234567"      // E.164 (international) - preferred
"0046701234567"     // International with 00 prefix
"0701234567"        // Swedish local format (converted to +46701234567)
```

---

## Permissions Structure

### Bluetooth Permissions
- `BLUETOOTH` - Basic Bluetooth API access
- `BLUETOOTH_ADMIN` - Enable/disable Bluetooth
- `BLUETOOTH_SCAN` (Android 12+) - Scan for devices
- `BLUETOOTH_CONNECT` (Android 12+) - Connect to devices

### SMS Permissions
- `SEND_SMS` - Send text messages
- `RECEIVE_SMS` - Receive SMS broadcasts
- `READ_SMS` - Read SMS from content provider

### File Permissions
- `READ_EXTERNAL_STORAGE` - Read from /sdcard/
- `WRITE_EXTERNAL_STORAGE` - Write to /sdcard/
- `MANAGE_EXTERNAL_STORAGE` (Android 11+) - Full file access

---

## Debugging

### Logcat Filtering

```bash
# View all SBMS logs
adb logcat -s SBMSBluetoothService:* SBMSMainActivity:* SMSManager:*

# Or by tag prefix
adb logcat | grep SBMS

# Save to file
adb logcat -s SBMSBluetoothService:* > sbms_logs.txt
```

### Common Issues

**Issue**: Service not detecting Bluetooth files
- **Cause**: Wrong folder path for device/Android version
- **Fix**: Manually check where files appear, add to `BLUETOOTH_OPP_PATHS` list

**Issue**: SMS not sending
- **Cause**: Missing `SEND_SMS` permission, SIM card locked
- **Fix**: Check logcat, verify permissions granted, try manual SMS from Messages app

**Issue**: vCard parsing fails
- **Cause**: Invalid X-SBMS-* property format
- **Fix**: Check vCard file with text editor, verify no special character issues

---

## Next Phase: J2ME App Development (Phase 2)

### Planned Structure

```
j2me/
├── src/
│   └── com/ckchdx/sbms/
│       ├── SBMSApp.java (MIDlet entry point)
│       ├── UI/
│       │   ├── MessageComposer.java
│       │   ├── ContactSelector.java
│       │   └── StatusDisplay.java
│       ├── Bluetooth/
│       │   └── OPPPushManager.java
│       ├── Util/
│       │   ├── VCardSerializer.java
│       │   ├── UUIDGenerator.java
│       │   └── PhoneNumberValidator.java
│       └── Storage/
│           └── FileManager.java
├── build/
└── build.xml (Ant build file)
```

### Key Challenges

1. **J2ME Sandbox** - Limited file system access
   - Solution: Use Samsung proprietary APIs or PIM API

2. **Bluetooth OPP Push** - E1310E as OPP client
   - Solution: Use standard JSR-82 Bluetooth API

3. **Memory Constraints** - ~2 MB heap
   - Solution: Keep .jar < 100 KB, avoid heavy libraries

---

## Testing Checklist

### Phase 1 (PoC - Manual)
- [ ] Pair Z Fold 6 with E1310E via Settings
- [ ] Manually send contact from E1310E to Z Fold 6
- [ ] Verify file appears in `/sdcard/Download/Bluetooth/`
- [ ] Manually send file from Z Fold 6 to E1310E
- [ ] Verify E1310E receives and stores file
- [ ] Repeat 20+ times, measure success rate

### Phase 3.1 (Android Reception)
- [ ] Start SBMS app on Z Fold 6
- [ ] Create test vCard file with X-SBMS-* properties
- [ ] Transfer to phone via Bluetooth
- [ ] Verify app detects file in 2-4 seconds
- [ ] Check logcat for parsing success
- [ ] Verify file is deleted after processing

### Phase 3.2 (End-to-End)
- [ ] E1310E sends message via OPP
- [ ] Z Fold 6 receives and parses
- [ ] SMS is sent to recipient
- [ ] Status response generated
- [ ] Response pushed back to E1310E
- [ ] E1310E displays "Message Sent ✓"

---

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| File Detection Latency | < 4 seconds | Polling interval 2s + processing |
| Message Parsing | < 500ms | Regex-based vCard parsing |
| SMS Send API | < 100ms | Queues message to system |
| Response Generation | < 500ms | Create vCard, prepare push |
| OPP Push Latency | 1-3 seconds | Bluetooth 2.0 transfer |
| **Total End-to-End** | **< 10 seconds** | From E1310E send to response display |

---

## Repository Structure

```
SBMS/
├── service.md                     # Original technical specification
├── IMPLEMENTATION_GUIDE.md        # This file
├── README.md                      # User-facing guide
├── android/                       # Android app (Phase 3)
│   ├── app/
│   │   ├── src/main/
│   │   │   ├── kotlin/com/ckchdx/sbms/
│   │   │   │   ├── MainActivity.kt
│   │   │   │   ├── model/SBMSMessage.kt
│   │   │   │   ├── service/SBMSBluetoothService.kt
│   │   │   │   ├── util/SMSManager.kt
│   │   │   │   └── receiver/BluetoothFileReceiver.kt
│   │   │   ├── res/
│   │   │   │   ├── layout/activity_main.xml
│   │   │   │   ├── values/strings.xml
│   │   │   │   └── values/colors.xml
│   │   │   └── AndroidManifest.xml
│   │   └── build.gradle.kts
│   └── build.gradle.kts
├── j2me/                         # J2ME app for E1310E (Phase 2, planned)
│   ├── src/
│   ├── build.xml
│   └── README.md
├── docs/                         # Documentation
│   ├── ARCHITECTURE.md
│   ├── TESTING.md
│   └── TROUBLESHOOTING.md
└── examples/                     # Example vCard files
    ├── message_valid.vcd
    ├── message_invalid.vcd
    └── response_example.vcd
```

---

## Contributing

### Branch Naming
- `android-phase3` - Android implementation
- `j2me-phase2` - J2ME implementation (planned)
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches

### Commit Messages
```
[PHASE-3] Add Bluetooth file monitor
[PHASE-2] Implement vCard serializer
[BUGFIX] Fix phone number validation regex
```

---

## References

- Bluetooth OPP Specification v1.1
- OBEX Protocol (IrDA/Bluetooth)
- Android SMS Manager Documentation
- vCard 2.1 Format (RFC 2425)
- JSR-82 Bluetooth for Java

---

## License

SBMS is proprietary research by Alex Jonsson (@CKCHDX)

---

**Last Updated**: December 11, 2025
**Current Version**: 0.1.0-alpha
