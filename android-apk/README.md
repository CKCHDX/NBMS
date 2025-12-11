# SBMS Android APK (Z Fold 6, Java)

Android 16 Java application that runs on the **Samsung Z Fold 6** and acts as the SMS relay + contact provider for SBMS.

## Role in System

- Receives SBMS vCard messages from E1310E via Bluetooth OPP
- Parses SBMS fields and sends real SMS using the Z Fold 6 SIM
- Provides a **full-featured messaging UI**:
  - Conversation list
  - Per-contact threads
  - Status indicators
- Exposes a contact sync mechanism to the E1310E
- Pushes delivery status and inbound SMS back to the E1310E

## Tech Stack

- Language: **Java** (no Kotlin)
- Min SDK: 26+ (target Android 16 / API level future-proof)
- Build system: Gradle (standard Android project layout)
- UI: Material Design 3, responsive for Z Fold 6

## Module Layout

```text
android-apk/
├── README.md
├── settings.gradle
├── build.gradle             # Top-level
├── app/
│   ├── build.gradle
│   ├── src/
│   │   ├── main/
│   │   │   ├── AndroidManifest.xml
│   │   │   ├── java/com/oscyra/sbms/android/
│   │   │   │   ├── MainActivity.java
│   │   │   │   ├── messaging/
│   │   │   │   │   ├── ConversationListActivity.java
│   │   │   │   │   ├── ThreadActivity.java
│   │   │   │   │   └── ComposeActivity.java
│   │   │   │   ├── bluetooth/
│   │   │   │   │   ├── OppServerService.java
│   │   │   │   │   ├── OppClientService.java
│   │   │   │   │   └── BtConnectionManager.java
│   │   │   │   ├── contacts/
│   │   │   │   │   ├── ContactSyncService.java
│   │   │   │   │   └── ContactProvider.java
│   │   │   │   ├── sms/
│   │   │   │   │   ├── SmsRelayService.java
│   │   │   │   │   ├── SmsStatusReceiver.java
│   │   │   │   │   └── SmsIncomingReceiver.java
│   │   │   │   └── util/
│   │   │   │       ├── VCardParser.java
│   │   │   │       └── SbmsUuid.java
│   │   │   └── res/
│   │   │       ├── layout/
│   │   │       ├── drawable/
│   │   │       └── values/
│   └── proguard-rules.pro
└── gradle/
    └── wrapper/
```

## Core Flows

### 1. Receive Message from E1310E → Send SMS

1. `OppServerService` listens for incoming OPP file pushes
2. When vCard file `message_*.vcd` is received:
   - `VCardParser` extracts:
     - `X-SBMS-TO`
     - `X-SBMS-TEXT`
     - `X-SBMS-UUID`
   - App shows confirmation UI or auto-send (configurable)
3. `SmsRelayService` uses `SmsManager` to send message
4. `SmsStatusReceiver` listens for `SENT` and `DELIVERED` broadcasts
5. A status vCard is generated and pushed back to E1310E via `OppClientService`

### 2. Contact Sync to E1310E

- Periodic job or manual action in app:
  - Query contacts provider (`ContactsContract`)
  - Serialize into SBMS contact vCards with `X-SBMS-CONTACT:true`
  - Push to E1310E over OPP

### 3. Remote UI from E1310E

- When user types on E1310E, Android app behaves like a remote SMS backend
- Android UI is still fully usable locally:
  - Start new threads
  - View history
  - Receive and reply to SMS

## Permissions

In `AndroidManifest.xml` (simplified):

```xml
<uses-permission android:name="android.permission.BLUETOOTH" />
<uses-permission android:name="android.permission.BLUETOOTH_ADMIN" />
<uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
<uses-permission android:name="android.permission.BLUETOOTH_ADVERTISE" />
<uses-permission android:name="android.permission.BLUETOOTH_SCAN" />

<uses-permission android:name="android.permission.SEND_SMS" />
<uses-permission android:name="android.permission.RECEIVE_SMS" />
<uses-permission android:name="android.permission.READ_SMS" />

<uses-permission android:name="android.permission.READ_CONTACTS" />
<uses-permission android:name="android.permission.WRITE_CONTACTS" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
```

Runtime permissions are requested from `MainActivity`.

## Build (CLI, No Android Studio)

You can build from **Windows 11** using only JDK + Gradle (no Android Studio UI required).

```bash
# From project root
cd android-apk

# Windows (PowerShell or cmd)
./gradlew.bat assembleDebug

# Result APK:
app/build/outputs/apk/debug/app-debug.apk
```

Install on Z Fold 6:

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

## UI / UX

- Z Fold 6 optimized layouts:
  - Two-pane layout for conversations on large screens
  - Adaptive layout for folded / unfolded states
- Material 3 components:
  - TopAppBar, NavigationRail, FAB
  - Snackbar for status
- Clear differentiation between:
  - **Local messages** (typed on Z Fold)
  - **Remote messages** (typed on E1310E via SBMS)

## Notes

- All code in this branch is **Java-only**
- No Android Studio project files are strictly required; Gradle handles everything
- Use `service.md` as the authoritative protocol reference for:
  - Message formats
  - OPP behavior
  - Status flow

## Next Steps (for you)

- Implement minimum skeleton classes and verify the app builds on Windows 11
- Implement `OppServerService` with a stub vCard parser and logcat output
- Verify E1310E can push **any** file to the Z Fold 6 via OPP
- Once transport is stable, wire into `SmsRelayService` to send real SMS
