# Samsung Bluetooth Message Service - Android (Z Fold 6)

## Overview

SBMS Android Application enables the Samsung Z Fold 6 to relay SMS messages to a paired Samsung E1310E device via Bluetooth OPP (Object Push Profile).

## Features

- **Bluetooth OPP Communication**: Establishes secure Bluetooth connection with E1310E
- **Contact Management**: Dynamically loads and displays contacts from phone
- **Message Routing**: Accepts vCard-formatted messages from E1310E and sends as native SMS
- **Status Tracking**: Provides delivery confirmation back to E1310E
- **Modern UI**: Clean, responsive Material Design interface
- **Database Storage**: Room database for message history and contact caching

## Architecture

```
src/main/java/com/oscyra/sbms/
├── MainActivity.java              # Main UI and orchestration
├── bluetooth/
│   └── BluetoothManager.java     # OPP connection & message handling
├── data/
│   ├── AppDatabase.java           # Room database
│   ├── Contact.java               # Contact entity
│   ├── ContactDao.java            # Contact data access
│   ├── Message.java               # Message entity
│   └── MessageDao.java            # Message data access
├── services/
│   └── SBMSMessageService.java    # Background service
├── receivers/
│   └── SmsReceiver.java           # SMS broadcast receiver
└── ui/
    └── ContactAdapter.java         # ListView adapter for contacts
```

## Building

### Prerequisites

- Android SDK 34 (API level 34)
- Android Build Tools 34.0.0+
- JDK 11+
- Gradle 8.1.0+

### Compile

```bash
# Clone repository and navigate to android-apk branch
git clone https://github.com/CKCHDX/SBMS.git
cd SBMS
git checkout android-apk

# Build APK (debug)
./gradlew assembleDebug

# Build APK (release)
./gradlew assembleRelease
```

Output APK: `build/outputs/apk/debug/app-debug.apk`

### Installation

```bash
# Install to connected device
adb install build/outputs/apk/debug/app-debug.apk

# Or run directly
./gradlew installDebug
```

## Configuration

### Bluetooth MAC Address

Edit `BluetoothManager.java` and update `getE1310EMacAddress()`:

```java
private String getE1310EMacAddress() {
    return "E1:31:0E:XX:XX:XX"; // Replace with actual E1310E MAC
}
```

To find E1310E MAC address:
1. Pair E1310E with Z Fold 6
2. Go to Settings → Bluetooth → Paired Devices
3. Note the MAC address

## Permissions Required

- `BLUETOOTH` - Bluetooth access
- `BLUETOOTH_ADMIN` - Bluetooth connection management
- `BLUETOOTH_SCAN` - Scan for devices (Android 12+)
- `BLUETOOTH_CONNECT` - Connect to devices (Android 12+)
- `SEND_SMS` - Send SMS messages
- `READ_CONTACTS` - Read contact list
- `READ_EXTERNAL_STORAGE` - Access Bluetooth files
- `WRITE_EXTERNAL_STORAGE` - Save message files

## Usage

1. Launch SBMS app on Z Fold 6
2. Tap "Connect to E1310E"
3. Select contact from list or search
4. Type message (max 160 characters)
5. Tap "Send Message"
6. App sends message via SMS immediately
7. E1310E receives delivery status via Bluetooth

## Message Protocol

Messages are exchanged as vCard 2.1 with custom X-SBMS-* properties:

```
BEGIN:VCARD
VERSION:2.1
PRODID:-//SBMS//1.0//EN
X-SBMS-MSG:true
X-SBMS-TO:+46701234567
X-SBMS-TEXT:Hello from E1310E
X-SBMS-PRIORITY:1
X-SBMS-TIMESTAMP:20251212T123000Z
X-SBMS-UUID:A3F7E2C1
END:VCARD
```

## Troubleshooting

### Connection Failed

- Verify Bluetooth is enabled
- Confirm E1310E is paired
- Check correct MAC address in code
- Ensure E1310E has OPP service enabled

### Message Not Sending

- Verify SMS permission granted
- Check contact phone number format (+46...)
- Ensure Bluetooth connection is active
- Check Z Fold 6 has cellular connectivity

### Contacts Not Loading

- Grant READ_CONTACTS permission
- Ensure contacts exist on device
- Check contact sync is enabled

## Testing

### Unit Tests

```bash
./gradlew test
```

### Integration Tests

```bash
./gradlew connectedAndroidTest
```

## Performance Notes

- Message transfer: 1-3 seconds
- SMS send: 2-5 seconds (cellular dependent)
- Bluetooth reconnect: 3-5 seconds
- Contact list update: <1 second

## Future Enhancements

- [ ] Multi-part message support (>160 chars)
- [ ] Message delivery receipts
- [ ] Bluetooth auto-reconnect
- [ ] Contact sync from E1310E
- [ ] Message templates
- [ ] Read receipts
- [ ] Message search and filtering
- [ ] Contact groups

## License

MIT License - See LICENSE file

## Author

Alex Jonsson - @CKCHDX
https://github.com/CKCHDX/SBMS
