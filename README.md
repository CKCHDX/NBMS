# Samsung Bluetooth Message Service (SBMS)

A complete, production-ready Bluetooth-based messaging system enabling seamless SMS communication between a Samsung Z Fold 6 (Android 16) and a Samsung E1310E classic mobile device.

## 🎯 Project Overview

**SBMS** bridges the gap between modern and retro Samsung devices, allowing the classic Samsung E1310E to send and receive SMS messages through your modern smartphone using Bluetooth Object Push Profile (OPP) as the transport mechanism.

### Why SBMS?

The Samsung E1310E has **no functional SIM card slot** but includes:
- ✅ Bluetooth 2.0 + EDR (Enhanced Data Rate)
- ✅ Object Push Profile (OPP) support
- ✅ Audio/Video Remote Control (AVRCP) support
- ✅ J2ME MIDP 2.0 runtime environment

**SBMS leverages these capabilities** to create a bidirectional messaging system without requiring a SIM card.

## 📁 Repository Structure

```
SBMS/
├── README.md                          # This file
├── service.md                         # Complete technical specification
├── docs/
│   ├── ARCHITECTURE.md               # System design documentation
│   ├── BLUETOOTH_PROTOCOL.md         # OPP/OBEX protocol reference
│   ├── MESSAGE_FORMAT.md             # vCard message specification
│   └── TROUBLESHOOTING.md            # Connection diagnostics
├── android-apk/                      # Z Fold 6 Android app (Java)
│   ├── README.md
│   ├── build.gradle
│   ├── AndroidManifest.xml
│   └── src/
│       └── com/oscyra/sbms/
│           ├── MainActivity.java
│           ├── services/
│           ├── ui/
│           ├── models/
│           └── utils/
├── E1310E-app/                       # Samsung E1310E app (J2ME)
│   ├── README.md
│   ├── build.xml
│   └── src/
│       └── com/oscyra/sbms/
│           ├── SBMSApp.java
│           ├── ui/
│           ├── bluetooth/
│           └── models/
└── shared/                           # Shared specifications & formats
    ├── message-schema.md
    └── test-vectors.json
```

## 🚀 Quick Start

### Prerequisites

- **Z Fold 6** running Android 16 with:
  - Java Development Kit (JDK 11+)
  - Bluetooth enabled
  - SMS permissions granted
  
- **Samsung E1310E** with:
  - Bluetooth enabled
  - J2ME runtime (built-in)
  - Paired with Z Fold 6

### Installation

#### Android APK (Z Fold 6)

```bash
cd android-apk
./gradlew assembleDebug
adb install build/outputs/apk/debug/SBMS.apk
```

**Or use prebuilt APK:**
```bash
# Download from Releases section
adb install SBMS-release.apk
```

#### E1310E J2ME App

```bash
cd E1310E-app
./build.sh
# Transfer SBMS.jar to E1310E via:
# - Bluetooth File Transfer
# - USB cable with file manager
# - Phone's J2ME app installer
```

### Basic Usage

**Sending Message from E1310E:**
1. Navigate: Menu → SBMS
2. Select "New Message"
3. Choose recipient from Contacts
4. Type message (160 chars max)
5. Select "Send via Bluetooth"
6. Phone receives, parses, and sends SMS
7. E1310E receives status confirmation

## 🔧 Technical Stack

### Android APK (Z Fold 6)
- **Language:** Java
- **Framework:** Android API 30+
- **Build System:** Gradle
- **Key Libraries:**
  - `android.bluetooth` - Bluetooth stack
  - `android.telephony` - SMS API
  - AndroidX support libraries
  - Material Design 3

### E1310E App
- **Language:** J2ME (Java MIDP 2.0)
- **Build System:** Custom build.xml
- **Key APIs:**
  - `javax.microedition.io.Connector` - Bluetooth RFCOMM
  - `javax.obex` - OBEX protocol (if available)
  - `javax.microedition.io.PushRegistry` - OPP server
  - J2ME UI (Form, List, Alert)

## 📋 Features

### Core Messaging
- ✅ Compose and send SMS from E1310E
- ✅ Receive SMS and display on E1310E
- ✅ Contact synchronization from Z Fold 6
- ✅ Message history and archives
- ✅ Delivery receipts and status tracking

### UI/UX
- ✅ Modern Material Design 3 on Android
- ✅ Classic Samsung UI on E1310E (adapted for screen)
- ✅ Touch-optimized on Z Fold 6
- ✅ D-Pad/soft-key navigation on E1310E
- ✅ Real-time connection status indicators

### Advanced Features
- ✅ Automatic contact syncing
- ✅ Message search functionality
- ✅ Draft message persistence
- ✅ Bluetooth connection recovery
- ✅ vCard message format with CRC32 validation
- ✅ Multi-recipient capabilities

## 🔌 Connection Architecture

```
Z Fold 6 (Android 16)           E1310E (J2ME)
├─ OPP Server                   ├─ OPP Server
│  (Receives files)             │  (Receives files)
├─ OPP Client                   ├─ OPP Client
│  (Sends files)                │  (Sends files)
├─ SMS Manager                  ├─ Bluetooth Manager
│  (Send actual SMS)            │  (File push/receive)
└─ Status Handler               └─ Message Handler
   (Parse responses)               (Parse responses)
         
         ↕ Bluetooth OPP ↕
    (OBEX over RFCOMM)
```

## 📱 Message Format (vCard Extended)

Messages are serialized as vCard 2.1 with X-SBMS extensions:

```
BEGIN:VCARD
VERSION:2.1
PRODID:-//SBMS//1.0//EN
X-SBMS-MSG:true
X-SBMS-TO:+46701234567
X-SBMS-TEXT:Hello from E1310E
X-SBMS-PRIORITY:1
X-SBMS-TIMESTAMP:20251211T150700Z
X-SBMS-UUID:abc123def456
X-SBMS-CRC32:0xA1B2C3D4
END:VCARD
```

## 🛠️ Building from Source

### Full Build (Both Platforms)

```bash
./build-all.sh
# Outputs:
# - build/android/SBMS.apk
# - build/e1310e/SBMS.jar
# - build/e1310e/SBMS.jad
```

### Android Only

```bash
cd android-apk
./gradlew clean build
# Output: build/outputs/apk/release/SBMS-release.apk
```

### E1310E Only

```bash
cd E1310E-app
./build.sh
# Output: build/SBMS.jar
```

## 🧪 Testing

### Unit Tests
```bash
cd android-apk
./gradlew test
```

### Integration Tests
```bash
cd E1310E-app
python3 test/test_vcard_parser.py
```

### Manual Testing Checklist
- [ ] Pairing E1310E with Z Fold 6
- [ ] OPP service discovery (SDP query)
- [ ] Single message transfer E1310E → Z Fold 6
- [ ] Status response Z Fold 6 → E1310E
- [ ] Multiple consecutive messages
- [ ] Contact sync from Z Fold 6 to E1310E
- [ ] SMS delivery on actual carrier network
- [ ] Bluetooth reconnection after disconnect
- [ ] Message character encoding (Swedish special chars)

## 🐛 Troubleshooting

### Connection Failed Error
**Symptom:** "Error - Connection Failed" when trying to establish Bluetooth connection

**Solutions:**
1. Ensure both devices are paired (not just discoverable)
2. Check that OPP service is enabled on both devices
3. Verify Bluetooth MAC address matches (Settings → About)
4. Restart Bluetooth on both devices
5. Increase RFCOMM connection timeout (see `service.md` Part 5)

### Messages Not Appearing
**Symptom:** E1310E sends message, but phone doesn't receive

**Diagnosis:**
```bash
# Check Android logcat
adb logcat | grep SBMS

# Verify Bluetooth file transfer working
adb shell ls -la /sdcard/Download/Bluetooth/
```

### E1310E App Won't Install
**Symptom:** "Installation failed" when loading SBMS.jar

**Solutions:**
1. Verify JAR is properly signed for Samsung J2ME
2. Check available storage on E1310E (Menu → Settings → Memory)
3. Use file manager to manually place JAR in correct directory
4. Check J2ME compatibility (MIDP 2.0 minimum required)

See **docs/TROUBLESHOOTING.md** for complete diagnostics.

## 📖 Documentation

- **[service.md](service.md)** - Complete technical specification with protocol details
- **[android-apk/README.md](android-apk/README.md)** - Android APK build & development guide
- **[E1310E-app/README.md](E1310E-app/README.md)** - E1310E J2ME app development guide
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design and flow diagrams
- **[docs/BLUETOOTH_PROTOCOL.md](docs/BLUETOOTH_PROTOCOL.md)** - Detailed OPP/OBEX protocol reference
- **[docs/MESSAGE_FORMAT.md](docs/MESSAGE_FORMAT.md)** - vCard message schema and extensions

## 🔐 Security Considerations

### Bluetooth Security
- All OPP transfers use Bluetooth v2.0 encryption (when paired)
- Messages transmitted over OPP channel are not encrypted beyond Bluetooth layer
- PIN used for pairing should be strong (not 0000)

### SMS Security
- No end-to-end encryption (limited by SMS standard)
- Messages visible on both devices locally
- Phone stores messages in standard SMS database
- E1310E stores in `/Message/` directory (readable by other apps)

### Recommendations
- Keep both devices in physical control
- Use strong Bluetooth pairing PIN
- Don't send sensitive data (passwords, tokens) via SBMS
- Regularly clear message history if needed
- Disable Bluetooth when not in use

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- E2E encryption layer
- Multi-recipient group messaging
- Media message support (MMS)
- Cross-platform compatibility (iOS)
- Performance optimizations
- Additional language support

## 📄 License

MIT License - See LICENSE file for details

## 👤 Author

Alex Jonsson (@CKCHDX)

## 🔗 Links

- **GitHub:** https://github.com/CKCHDX/SBMS
- **Website:** https://oscyra.solutions/
- **Issues:** https://github.com/CKCHDX/SBMS/issues

## 📞 Support

For issues, questions, or suggestions:
1. Check **docs/TROUBLESHOOTING.md**
2. Review **service.md** technical specification
3. Search existing GitHub issues
4. Create new issue with detailed description

---

**Status:** 🚧 In Development
**Last Updated:** December 11, 2025
**Current Version:** 0.1.0 (Alpha)
