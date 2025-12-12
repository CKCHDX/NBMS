# SBMS Project Structure

## Repository Layout

```
SBMS/
├── main                          # Primary branch - documentation
├── android-apk                  # Z Fold 6 Android application
├── E1310E-app                   # Samsung E1310E J2ME application
├── android-phase3               # (Deprecated) Earlier Android version
├── service.md                    # Complete technical specification
├── README.md                     # Main documentation
├── PROJECT_STRUCTURE.md         # This file
└── LICENSE

## Branch Organization

### main
**Purpose**: Documentation, specifications, and project coordination

**Contents**:
- service.md - Technical specification
- README.md - Project overview
- PROJECT_STRUCTURE.md - This file
- Architecture diagrams
- Build instructions

**Workflow**:
1. Create branches from main for features
2. Merge back when complete
3. Tag releases

### android-apk
**Platform**: Android 12+ (API 34), Kotlin/Java
**Device**: Samsung Z Fold 6
**Purpose**: Relay SMS messages to E1310E via Bluetooth OPP

**Project Structure**:
```
android-apk/
├── build.gradle                 # Gradle configuration
├── settings.gradle
├── proguard-rules.pro
├── src/main/
│   ├── AndroidManifest.xml
│   ├── java/com/oscyra/sbms/
│   │   ├── MainActivity.java         # Main UI & orchestration
│   │   ├── bluetooth/
│   │   │   └── BluetoothManager.java    # OPP communication
│   │   ├── data/
│   │   │   ├── AppDatabase.java        # Room database
│   │   │   ├── Contact.java
│   │   │   ├── ContactDao.java
│   │   │   ├── Message.java
│   │   │   └── MessageDao.java
│   │   ├── services/
│   │   │   └── SBMSMessageService.java  # Background service
│   │   ├── receivers/
│   │   │   └── SmsReceiver.java        # SMS handler
│   │   ├── ui/
│   │   │   └── ContactAdapter.java      # ListView adapter
│   │   └── utils/
│   │       └── SBMSMessageFormatter.java
│   ├── res/
│   │   ├── layout/
│   │   │   ├── activity_main.xml
│   │   │   └── contact_list_item.xml
│   │   ├── values/
│   │   │   ├── colors.xml
│   │   │   └── strings.xml
│   │   └── drawable/
└── README-ANDROID.md

**Build**: Gradle (Android Studio compatible)
**Output**: APK (signed/unsigned)
**Min Size**: ~3-5 MB
```

### E1310E-app
**Platform**: J2ME MIDP 2.0 (CLDC 1.1)
**Device**: Samsung E1310E
**Purpose**: Compose SMS messages and send via Bluetooth OPP

**Project Structure**:
```
E1310E-app/
├── build.xml                    # Ant build configuration
├── manifest.mf
├── src/com/oscyra/sbms/
│   ├── SBMSApp.java              # MIDlet entry point
│   ├── MainScreen.java           # Primary UI form
│   ├── bluetooth/
│   │   └── BluetoothHandler.java    # OPP protocol
│   ├── storage/
│   │   ├── StorageManager.java      # File I/O
│   │   ├── Contact.java
│   │   └── ContactManager.java      # Contact operations
│   └── ui/
│       ├── MessageComposer.java     # vCard formatter
│       └── ContactSelector.java     # Contact picker
├── build/                      # Compiled .class files
├── dist/
│   ├── SBMS.jar                # Compiled application
│   └── SBMS.jad                # Deployment descriptor
├── README-E1310E.md
├── COMPILATION.md
└── TESTING.md

**Build**: Ant + J2ME WTK
**Output**: JAR (preverified)
**Max Size**: ~100 KB (device constraint)
```

## Technology Stack

### Android Application (Z Fold 6)

| Component | Technology | Version |
|-----------|-----------|----------|
| Language | Java/Kotlin | 11 |
| SDK | Android SDK | 34 |
| Build System | Gradle | 8.1 |
| Minimum API | Android 12 | API 31 |
| Target API | Android 14 | API 34 |
| Database | Room ORM | 2.6.1 |
| Bluetooth | Android BT API | 1.0 |
| UI Framework | AndroidX | Latest |
| Test Framework | JUnit/Espresso | 4.13.2 |

**Key Dependencies**:
- androidx.appcompat:appcompat
- androidx.room:room-runtime
- androidx.lifecycle:lifecycle-*
- com.google.android.material:material
- com.google.code.gson:gson

### E1310E Application

| Component | Technology | Version |
|-----------|-----------|----------|
| Language | Java | 1.4-1.6 |
| Profile | MIDP | 2.0 |
| Configuration | CLDC | 1.1 |
| Build System | Ant | 1.9+ |
| J2ME Toolkit | WTK | 2.5.2 |
| Bluetooth | JSR-82 | 1.0 |
| I/O | JSR-75 | 1.0 |
| Max Heap | Device | ~200 KB |

**Compatible Devices**:
- Samsung E1310E
- Samsung E2210
- Samsung F700
- Any MIDP 2.0 device with Bluetooth

## Communication Protocol

### Message Flow

```
E1310E                          Network                    Z Fold 6
  |                                                           |
  |------ Compose Message ------>                             |
  |                          (Local)                          |
  |-- Serialize as vCard -------->                            |
  |                                                           |
  |-------- Bluetooth OPP -------> |----->|                  |
  |                               (RFCOMM+OBEX)              |
  |                                       |--- Parse vCard ---|>
  |                                       |--- Send SMS ------>|
  |                                       |                   |~~~> Network
  |                                       |<--- SMS Result ----<
  |<-------- Bluetooth OPP ---------- |------|                |
  |   (Status Response)                                       |
  |-- Display Confirmation --->|                             |
  |                                                           |
```

### Message Format (vCard 2.1 Extended)

```
BEGIN:VCARD
VERSION:2.1
PRODID:-//SBMS//1.0//EN
X-SBMS-MSG:true
X-SBMS-TO:+46701234567
X-SBMS-TEXT:Hello from E1310E
X-SBMS-PRIORITY:1
X-SBMS-TIMESTAMP:20251212T150000Z
X-SBMS-UUID:A3F7E2C1
END:VCARD
```

## Bluetooth Profile Details

### OPP (Object Push Profile)

**UUID**: 1105-0000-1000-8000-00805f9b34fb
**RFCOMM Channel**: Dynamic (discovered via SDP)
**Protocol**: OBEX (Object Exchange)
**Max Transfer**: 4 MB per file
**Typical Speed**: 400-500 KB/s

### Connection Parameters

| Parameter | Value |
|-----------|-------|
| Bluetooth Version | 2.0 + EDR |
| Class | 1 (10m range) |
| Supported Profiles | OPP, AVRCP, SPP |
| Pairing Required | Yes |
| Encryption | Device default |
| Authentication | Pairing PIN |

## Data Model

### Contact Entity (Android)

```java
@Entity(tableName = "contacts")
class Contact {
    @PrimaryKey int id;
    String displayName;
    String phoneNumber;
    long lastMessageTime;
}
```

### Message Entity (Android)

```java
@Entity(tableName = "messages")
class Message {
    @PrimaryKey int id;
    String senderPhoneNumber;
    String recipientPhoneNumber;
    String messageText;
    long timestamp;
    boolean isSent;
    String uuid;
    String status;  // PENDING, SENT, DELIVERED, FAILED
}
```

### Contact (E1310E)

```java
class Contact {
    String displayName;
    String phoneNumber;
    long lastMessageTime;
}
```

## Build & Deployment Workflow

### Android Workflow

```bash
# 1. Clone and setup
git clone https://github.com/CKCHDX/SBMS.git
cd SBMS
git checkout android-apk

# 2. Build
./gradlew assembleDebug

# 3. Install
adb install build/outputs/apk/debug/app-debug.apk

# 4. Run
adb shell am start -n com.oscyra.sbms/.MainActivity
```

### E1310E Workflow

```bash
# 1. Clone and setup
git clone https://github.com/CKCHDX/SBMS.git
cd SBMS
git checkout E1310E-app

# 2. Configure WTK path
vi build.xml  # Set wtk.home

# 3. Build
ant jar

# 4. Deploy via Bluetooth OPP
obexftp -b E1:31:0E:XX:XX:XX -p dist/SBMS.jar

# OR via HTTP
cp dist/SBMS.* /var/www/html/sbms/
# Then access from phone: http://server/sbms/SBMS.jad
```

## Development Guidelines

### Code Style

**Android (Java/Kotlin)**:
- Google Java Style Guide
- Max line length: 100 characters
- Naming: camelCase for methods/variables, PascalCase for classes
- Documentation: Javadoc for public APIs

**E1310E (Java)**:
- Java 1.4 compatible
- No generics, use Vector/Hashtable
- Minimal memory footprint
- Javadoc documentation

### Git Workflow

1. Create feature branch from main:
   ```bash
   git checkout -b feature/my-feature
   ```

2. Commit regularly with descriptive messages:
   ```bash
   git commit -m "Add Bluetooth connection pooling for E1310E"
   ```

3. Push and create Pull Request

4. Merge to target branch (android-apk or E1310E-app)

### Testing Strategy

**Unit Tests**:
- Android: JUnit + Mockito
- E1310E: JUnit (emulator)

**Integration Tests**:
- Bluetooth connectivity
- Message end-to-end flow
- Contact synchronization

**Acceptance Tests**:
- User workflows on actual devices
- Edge cases (disconnects, message loss)
- Performance benchmarks

## Performance Targets

| Operation | Target | Actual |
|-----------|--------|--------|
| Bluetooth Connect | <5s | ~3-5s |
| Message Send | <3s | ~1-2s |
| Status Response | <3s | ~2-3s |
| Contact Load | <2s | ~1s |
| App Launch | <5s | ~2-3s |
| **Total Round Trip** | **<15s** | **~8-13s** |

## Security Considerations

1. **Bluetooth Security**
   - Uses device pairing
   - No additional encryption in current version
   - Plan: Add vCard encryption in v2.0

2. **Data Privacy**
   - Phone numbers transmitted in clear
   - SMS content in clear
   - Plan: End-to-end encryption in v2.0

3. **Authentication**
   - Relies on Bluetooth pairing
   - No app-level authentication
   - Suitable for personal/trusted use

## Limitations & Future Work

### Current Limitations

1. E1310E has no SIM card (requires relay)
2. 160 character limit (standard SMS)
3. Text only (no MMS/media)
4. Single Bluetooth connection
5. No auto-reconnect on disconnect
6. No message encryption

### Planned Enhancements (v2.0+)

- [ ] Multi-part message support
- [ ] Message encryption
- [ ] Contact sync from phone PBAP
- [ ] Delivery receipts
- [ ] Message search and filtering
- [ ] Contact groups
- [ ] Message templates
- [ ] Auto-reconnect on disconnect
- [ ] MMS support (Android only)
- [ ] Message scheduling

## Resources

### Documentation
- service.md - Technical specification
- README-ANDROID.md - Android-specific guide
- README-E1310E.md - E1310E-specific guide
- COMPILATION.md - Build instructions

### External Resources
- Bluetooth SIG Specs: https://www.bluetooth.com/
- Android Developers: https://developer.android.com/
- J2ME Documentation: https://docs.oracle.com/javame/
- WTK User Guide: /opt/WTK2.5.2/doc/

## Support & Contact

- **Issues**: https://github.com/CKCHDX/SBMS/issues
- **Email**: alex@oscyra.solutions
- **Website**: https://oscyra.solutions/
