# SBMS E1310E App (J2ME)

J2ME MIDP 2.0 application that runs on the **Samsung E1310E** and acts as the remote SMS composer and status viewer for SBMS.

## Role in System

- Provides UI to compose SMS messages on E1310E
- Lets user pick recipients from:
  - Local phonebook (if API allows), and/or
  - Synchronized contacts from Z Fold 6
- Serializes messages into SBMS vCard format
- Pushes messages to the Android side via Bluetooth OPP
- Receives status vCards and displays delivery state

## Tech Stack

- Platform: **J2ME MIDP 2.0**, CLDC 1.1
- Device: Samsung E1310E
- Tooling: Any J2ME toolchain (WTK, Ant, or custom) as long as it produces `.jar + .jad`

## Module Layout

```text
E1310E-app/
├── README.md
├── build.xml              # Ant build (or equivalent)
├── src/
│   └── com/oscyra/sbms/e1310e/
│       ├── SBMSMidlet.java
│       ├── ui/
│       │   ├── MainMenuScreen.java
│       │   ├── ComposeScreen.java
│       │   ├── ContactListScreen.java
│       │   ├── MessageListScreen.java
│       │   └── StatusScreen.java
│       ├── bt/
│       │   ├── BluetoothManager.java
│       │   ├── OppClient.java
│       │   └── OppServerListener.java
│       ├── model/
│       │   ├── Contact.java
│       │   ├── Message.java
│       │   └── Status.java
│       └── util/
│           ├── VCardSerializer.java
│           └── SbmsUuid.java
└── res/
    └── icons, strings (if used)
```

## Core Flows

### 1. Compose & Send Message

1. User opens **SBMS** on E1310E
2. Main menu options:
   - "New Message"
   - "Inbox"
   - "Sent"
   - "Contacts (Synced)"
   - "Connection Status"
3. "New Message" → `ComposeScreen`:
   - Select contact (local or synced)
   - Enter up to 160 characters
   - Press "Send via Bluetooth"
4. `VCardSerializer` builds SBMS vCard:

```text
BEGIN:VCARD
VERSION:2.1
PRODID:-//SBMS//1.0//EN
X-SBMS-MSG:true
X-SBMS-TO:+4670XXXXXXX
X-SBMS-TEXT:Hello from E1310E
X-SBMS-PRIORITY:1
X-SBMS-TIMESTAMP:20251211T150700Z
X-SBMS-UUID:ABC12345
END:VCARD
```

5. `OppClient` pushes this file to the paired Z Fold 6 over OPP
6. Message stored in local `Sent` list

### 2. Receive Status & Inbox

- `OppServerListener` monitors incoming OPP pushes
- When a status vCard arrives:
  - Parse `X-SBMS-UUID`, `X-SBMS-STATUS`, `X-SBMS-DELIVERY`
  - Match against local `Message` using UUID
  - Update status (e.g., "SENT", "DELIVERED", "FAILED")
  - Notify user via `StatusScreen` or alert

### 3. Contact Sync

- SBMS on Android can push batched contact vCards
- `OppServerListener` parses `X-SBMS-CONTACT` entries and stores them in local contact list
- Contact list is navigated by D-pad / soft keys

## UI / UX Design

- Follow classic Samsung feature-phone UI paradigms:
  - Softkey labels: `Left = Select/OK`, `Right = Back/Cancel`
  - D-pad navigation for lists and fields
  - Single-column list views for contacts/messages
- Keep screens **lightweight** to avoid memory issues
- Use message length counter (`"123/160"`) while typing

## Build

Example Ant usage (to be adapted to your environment):

```bash
ant clean jar
# Output: dist/SBMS.jar and SBMS.jad
```

Then transfer to the E1310E using **Bluetooth OPP** or whatever loader you prefer.

## Notes & Constraints

- J2ME sandbox can be restrictive; filesystem and contacts APIs might be limited.
- If direct phonebook access is blocked, rely on **synced contacts from Android**.
- OPP behavior may vary; using vCard `.vcf`/`.vcd` naming keeps compatibility high.
- vCard Option A from `service.md` is used initially for simplicity and debuggability.

## Next Steps (for you)

- Hook this layout into your existing J2ME toolchain
- Implement minimal `SBMSMidlet` shell and verify it launches on device/emulator
- Implement `OppClient` with a hard-coded test vCard and verify push to Android
- Iterate towards full messaging UI once the transport is 100% reliable.
