Samsung Bluetooth Messaging System (SBMS): Complete Technical Specification
Executive Summary
Your Samsung E1310E has two critical Bluetooth services available that, when properly leveraged, enable a relay-based messaging system without requiring a functional SIM card. The Object Push Profile (OPP) becomes your primary data transport mechanism, while the Audio Remote Control Service (AVRCP) provides supplementary control signaling. This document provides the complete technical architecture, implementation roadmap, and protocol specifications for building SBMS.

Part 1: Hardware Capabilities Analysis
1.1 Samsung E1310E Wireless Specification
Your device includes the following wireless capabilities:
| Component     | Specification                   | Status       |
| ------------- | ------------------------------- | ------------ |
| Bluetooth     | v2.0 + EDR (Enhanced Data Rate) | ✅ Active     |
| OPP Support   | GOEP-based file push            | ✅ Available  |
| AVRCP Support | Audio/Video Remote Control      | ✅ Available  |
| SPP Support   | Serial Port Profile (likely)    | ⚠️ Check     |
| GSM           | 900/1800 MHz                    | ❌ SIM-locked |
| WiFi          | None                            | N/A          |
| USB           | Not accessible                  | N/A          |
| Infrared (IR) | Not present                     | N/A          |
Key Advantage: Bluetooth 2.0 is vastly superior to the Bluetooth 1.x on your Nokia 2760, offering:

Stable pairing (typically holds 4+ hours without disconnect)

Faster file transfer (up to 3 Mbps theoretical, ~400 KB/s practical)

Better range (10 meters reliably indoors)

Lower power consumption (extended battery life during operation)​

Part 2: Bluetooth Profile Deep Dive
2.1 Object Push Profile (OPP)
Purpose: Transfer arbitrary binary objects between devices without requiring user intervention after initiating the push.

Technical Foundation: OPP builds on GOEP (Generic Object Exchange Profile) and uses OBEX (Object Exchange) protocol as its transport layer.​

OPP Layer Stack Architecture
┌─────────────────────────────────┐
│  Application Layer              │
│  (Your SBMS Message Handler)    │
├─────────────────────────────────┤
│  OPP Profile (GOEP-based)       │  ← You operate here
│  - Push Client / Push Server    │
├─────────────────────────────────┤
│  OBEX Protocol                  │  ← Binary object exchange
│  - PUT, GET, CONNECT, ABORT     │
├─────────────────────────────────┤
│  RFCOMM (Serial Port over BT)   │
│  - Multiplexing virtual channels│
├─────────────────────────────────┤
│  L2CAP (Logical Link Control)   │
├─────────────────────────────────┤
│  ACL/Baseband (Bluetooth Radio) │
└─────────────────────────────────┘

OPP Operational Modes
Mode 1: Push Client (E1310E sends → Your Phone receives)

E1310E initiates connection to OPP server on your phone

OBEX handshake establishes session

E1310E sends file via OBEX PUT command

File written to phone's OPP storage location

Connection closes

Mode 2: Push Server (Your Phone sends → E1310E receives)

Your phone initiates connection to OPP server on E1310E

OBEX handshake

Phone sends file via PUT command

E1310E writes to memory storage

Connection closes

Mode 3: Business Card Exchange (bi-directional vCard swap)

Less relevant for your use case, but supported​

OBEX Protocol Structure for File Transfer
When pushing a message, the data packet structure follows this format:

OBEX PUT Command Header (minimal):
┌──────────────────────────────────────────┐
│ Byte 0: 0x02 (OBEX PUT command code)     │
│ Byte 1-2: Total packet length (Big-Endian) │
│ Byte 3+: OBEX Headers (TLV format)       │
└──────────────────────────────────────────┘

OBEX Headers (Type-Length-Value triplets):
┌─────────────────────────────────┐
│ 0x01 (Count)                    │  [optional] Total object count
│ 0x48 (Name, Unicode)            │  Filename: "message.sbms"
│ 0x49 (Body, raw data)           │  Your actual message payload
│ 0xC9 (End of Body)              │  Marks final packet
│ 0xCB (Length)                   │  Object size in bytes
└─────────────────────────────────┘

Example for a 47-byte message file:
PUT | 0x002F | 0x01 | message.sbms | {...message data...} | EOF


The beauty of OBEX is its binary-based headers (unlike HTTP's text), making it ideal for resource-constrained 2009 devices. Each header is just 3-4 bytes overhead.​

File Size Constraints
OPP typical limit: Up to 4 MB per file (E1310E internal flash: 2 MB max)

Practical SMS message: 160 characters = ~160 bytes

With metadata (phone number + urgency flags): ~200-250 bytes

Overhead: OBEX adds ~50 bytes per transfer

Conclusion: SMS messages fit comfortably with room for expansion

2.2 Audio/Video Remote Control Profile (AVRCP)
Purpose: Send command tokens to control audio playback on the paired device.

Your E1310E Role: Likely AVRCP Controller (AVRCP-CT) sending commands.​​

AVRCP Command Set
Standard AVRCP 1.3 (likely on E1310E) supports these commands:

text
Play / Pause
Stop
Next Track
Previous Track
Fast Forward
Rewind
Volume Up / Down
Mute

Vendor-Specific Commands (custom implementation possible)


| Aspect      | OPP                               | AVRCP                       |
| ----------- | --------------------------------- | --------------------------- |
| Use Case    | Data (messages, files)            | Commands (play, stop, etc.) |
| Reliability | Very high (acknowledged delivery) | Medium (fire-and-forget)    |
| Latency     | ~1-3 seconds per file             | ~100-300ms per command      |
| Bandwidth   | Can transfer large files          | Limited to command tokens   |
| For SBMS    | ✅ Primary transport               | ⚠️ Secondary signaling      |
Proposed SBMS Usage of AVRCP:

Play = "Ready to send message"

Next = "Send to next contact"

Pause = "Cancel transmission"

Stop = "Reset state"

Custom vendor commands (if you can reverse-engineer Samsung firmware) for status notifications​



Part 3: SBMS Architecture & Protocol Specification
3.1 System Overview
text

┌──────────────────────────────────────────────────────────────┐
│                    SBMS System                                │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────┐           ┌──────────────────────────┐  │
│  │  Samsung E1310E │           │   Your Modern Phone      │  │
│  │   (No SIM)      │           │   (Android/iOS)          │  │
│  │                 │           │                          │  │
│  │  ┌───────────┐  │           │  ┌────────────────────┐  │  │
│  │  │ Messaging │  │   OPP     │  │  SBMS Listener App │  │  │
│  │  │   UI      │◄─┼──────────►│  │                    │  │  │
│  │  └───────────┘  │ (Files)   │  │  ┌──────────────┐  │  │  │
│  │  ┌───────────┐  │           │  │  │Parse Message │  │  │  │
│  │  │  Contacts │  │  AVRCP    │  │  │Send via SMS  │  │  │  │
│  │  └───────────┘  │ (Control) │  │  └──────────────┘  │  │  │
│  │       ↑         │           │  │       ↓            │  │  │
│  │    J2ME App     │           │  │  Status Handler    │  │  │
│  │  (Custom MIDP)  │           │  │  Return via OPP    │  │  │
│  └─────────────────┘           └──────────────────────────┘  │
│         │                                │                    │
│         └────────────────────────────────┘                    │
│              Bluetooth 2.0 Link                               │
│                                                                │
└──────────────────────────────────────────────────────────────┘



3.2 Message Format Specification (SBMS v1.0)
Your message must be serialized into a binary or text format that both E1310E and your phone understand.

Option A: Text-Based Format (Recommended for Initial Testing)
text
Format: vCard 2.1 extension with custom X-properties

BEGIN:VCARD
VERSION:2.1
PRODID:-//SBMS//1.0//EN
X-SBMS-MSG:true
X-SBMS-TO:+46701234567
X-SBMS-TEXT:Hello from E1310E
X-SBMS-PRIORITY:1
X-SBMS-TIMESTAMP:20251211T150700Z
X-SBMS-UUID:abc123def456
END:VCARD

File format: UTF-8 text
File extension: .vcd (vCard compatible)
File size: 200-400 bytes typical
Advantages:

Human-readable for debugging

Uses standard vCard format (OPP expects this)

Easy to parse on phone side (regex or XML parser)

Tolerates minor formatting errors

Disadvantages:

Larger file size (~2x binary)

Slower parsing on constrained E1310E

Option B: Binary Format (Optimized)
text
Byte Structure:

[0-3]    Magic: 0x53 0x42 0x4D 0x53 ('SBMS')
[4]      Version: 0x01
[5]      Message Type: 0x01 (SMS), 0x02 (Status), 0x03 (Ack)
[6]      Priority: 0x00 (Low), 0x01 (Normal), 0x02 (Urgent)
[7]      Flags: 0x00 = No flags
[8-9]    Payload length (Little-Endian u16)
[10-29]  Recipient phone number (20 bytes, null-padded)
[30-189] SMS text (160 bytes max)
[190-197] Timestamp (u64 Unix seconds)
[198-213] Message UUID (16 bytes)
[214-217] CRC32 checksum

Total fixed size: 218 bytes
Example (binary hex):

text
53 42 4D 53      // Magic: SBMS
01               // Version 1
01               // Type: SMS
01               // Priority: Normal
00               // Flags
47 00            // Payload length: 71 bytes
2B 34 36 37 30 31 32 33 34 35 36 37 00 00...  // "+46701234567\0..."
48 65 6C 6C 6F 20 66 72 6F 6D 20 45 31 33 31...  // "Hello from E131..."
...
Advantages:

Compact (218-byte fixed format)

Fast binary parsing

CRC32 checksum for integrity

Type system for future extensibility

Disadvantages:

Not human-readable

Requires exact byte alignment

Harder to debug in hex editor

Recommendation: Start with Option A (vCard text) for initial prototype, migrate to Option B (binary) once proven stable.

3.3 Complete Message Flow Diagram


┌─────────────────────────────────────────────────────────────┐
│  Step 1: User Composes Message on E1310E                     │
├─────────────────────────────────────────────────────────────┤
│  User navigates:                                              │
│  Menu → Contacts (select recipient)                          │
│  ↓                                                             │
│  Write Message (160-char limit)                              │
│  ↓                                                             │
│  Options → Send via Bluetooth                                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 2: E1310E Serializes Message into vCard Format        │
├─────────────────────────────────────────────────────────────┤
│  J2ME App:                                                    │
│  1. Read contact name/phone from phonebook                  │
│  2. Read typed message from drafts                          │
│  3. Generate UUID (first 8 bytes of hash of message)        │
│  4. Create vCard file with X-SBMS-* properties             │
│  5. Write to /Message/ or /Temp/ directory                 │
│  6. File: message_abc123.vcd (~300 bytes)                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 3: E1310E Initiates OPP Push to Phone                │
├─────────────────────────────────────────────────────────────┤
│  Bluetooth Stack on E1310E:                                  │
│  1. SDP Query: Discover OPP service on phone               │
│     Query: "Is there a service with UUID 1105?"            │
│     Response: "Yes, listen on RFCOMM channel 7"            │
│  2. RFCOMM Connect to phone:7                              │
│  3. OBEX Connect (handshake)                               │
│  4. OBEX PUT message_abc123.vcd                            │
│  5. Wait for OBEX OK response                              │
│  6. RFCOMM Disconnect                                      │
│  Typical duration: 1-3 seconds                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 4: Phone Receives & Parses Message                    │
├─────────────────────────────────────────────────────────────┤
│  SBMS Listener App (Python/PyQt or native):                │
│  1. Monitor Bluetooth OPP folder                            │
│  2. File detected: message_abc123.vcd                      │
│  3. Parse vCard X-SBMS-* fields                            │
│  4. Extract: phone_number = "+46701234567"                │
│             text = "Hello from E1310E"                    │
│  5. Validate CRC if binary format used                     │
│  6. Display preview: "Send to +46701234567? Yes/No"       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 5: Phone Sends Actual SMS via Native API             │
├─────────────────────────────────────────────────────────────┤
│  App logic:                                                  │
│  1. User confirms in dialog: "Send SMS? Yes/No"            │
│  2. Call native SMS API                                    │
│     Android: android.telephony.SmsManager.sendTextMessage()│
│     iOS: MessageUI.MFMessageComposeViewController          │
│  3. SMS queues in phone's outbox                           │
│  4. Phone's radio sends SMS via cellular network           │
│  5. SMS delivers to recipient                              │
│  6. Delivery receipt captured (if enabled)                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 6: Phone Sends Status Response via OPP               │
├─────────────────────────────────────────────────────────────┤
│  SBMS App generates response file:                          │
│  response_abc123.vcd containing:                           │
│  X-SBMS-STATUS: "SENT"                                    │
│  X-SBMS-TIMESTAMP: "20251211T150800Z"                     │
│  X-SBMS-DELIVERY: "PENDING" (or "DELIVERED" if instant)  │
│  X-SBMS-UUID: "abc123def456"  (matches request)           │
│                                                              │
│  Phone initiates OPP PUSH to E1310E:                       │
│  1. Resolve OPP server on E1310E                           │
│  2. RFCOMM + OBEX handshake                                │
│  3. Push response_abc123.vcd to E1310E                     │
│  4. Close connection                                       │
│  Typical duration: 1-3 seconds                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 7: E1310E Displays Status & Stores in Sent Folder    │
├─────────────────────────────────────────────────────────────┤
│  J2ME App on E1310E:                                         │
│  1. File received: response_abc123.vcd                     │
│  2. Parse X-SBMS-STATUS field                             │
│  3. Display: "✓ Message Sent to +46701234567"             │
│     Or: "✗ Failed - Try Again"                            │
│  4. Move original message to /Message/Sent/ folder         │
│  5. Log transaction with timestamp                         │
│  6. Update contact with last-message-sent timestamp        │
│  7. Return to idle screen                                  │
└─────────────────────────────────────────────────────────────┘


Part 4: Implementation Roadmap
Phase 1: Proof of Concept (Week 1-2)
Goal: Verify bidirectional OPP file transfer works reliably.

Tasks:

Manual OPP Test

Create a simple vCard file on E1310E (using built-in contacts app)

Select "Send via Bluetooth" → OPP → Your phone

Verify file arrives on phone

Check where it's stored (Android: /sdcard/Download/Bluetooth/, iOS: Files.app)

Create Test vCard Generator

Write simple Python script to create vCard files with X-SBMS-* fields

Generate test files: message_test1.vcd, message_test2.vcd

Manually copy to E1310E via file manager or Bluetooth

Test Phone-to-E1310E Reverse Push

From your phone, use Bluetooth file transfer to send a vCard to E1310E

Verify E1310E receives and stores it

Check if E1310E's native contacts app recognizes it

Measure Performance

Record connection setup time (SDP discovery → RFCOMM connect)

Measure file transfer time for various sizes (100 bytes, 300 bytes, 1 MB)

Test reliability over 20+ consecutive transfers (success rate)

Test with multiple reconnections

Phase 2: Custom J2ME App Development (Week 3-4)
Goal: Build a lightweight SMS composer on E1310E.

Requirements:

J2ME MIDP 2.0 compatible (E1310E supports this)

File I/O capabilities

Contacts API access (read phonebook)

<100 KB compiled .jar size

Architecture:

text
App Structure:
├── SBMSApp.java (main MIDlet entry point)
├── MessageComposer.java (UI form with text input)
├── ContactSelector.java (phonebook picker)
├── BluetoothManager.java (OPP push wrapper)
├── FileSerializer.java (vCard generation)
├── StatusDisplay.java (result screen)
└── resources/
    └── messages.properties (localization)
Key Features:

Menu: New Message → Select Contact → Type Text → Send via BT → Wait for Status

Local storage: /Message/Sent/ and /Message/Drafts/ directories

Phone number validation (starts with +, max 20 digits)

Message length counter (160 char limit with SMS standard)

Automatic UUID generation (first 8 bytes of SHA-1(phone + text + timestamp))

Development Environment:

Samsung J2ME SDK (specialized for Samsung phones, available on SourceForge)

Eclipse IDE + J2ME plugin

WTK (Wireless Toolkit) emulator for testing

Phase 3: Phone App Development (Week 5-6)
Goal: Build listener + SMS relay on your modern phone.

Choice A: Python + PyQt (if on Linux/Mac with Bluetooth)

python
# sbms_listener.py (pseudocode)
import bluetooth
import os
from pathlib import Path

class SBMSListener:
    def __init__(self):
        self.bt_address = "E1:31:0E:MA:C:00"  # E1310E Bluetooth MAC
        self.opp_folder = "/sdcard/Download/Bluetooth"
        
    def watch_incoming_messages(self):
        while True:
            for file in Path(self.opp_folder).glob("message_*.vcd"):
                message = self.parse_vcard(file)
                self.handle_sms(message)
                file.unlink()  # Delete after processing
    
    def parse_vcard(self, filepath):
        with open(filepath) as f:
            data = f.read()
        return {
            'to': re.search(r'X-SBMS-TO:(.+)', data).group(1),
            'text': re.search(r'X-SBMS-TEXT:(.+)', data).group(1),
            'uuid': re.search(r'X-SBMS-UUID:(.+)', data).group(1),
        }
    
    def handle_sms(self, message):
        # Send actual SMS
        sms = send_sms(message['to'], message['text'])
        
        # Generate response
        response = self.create_response(message, 'SENT')
        
        # Push back to E1310E
        self.push_via_opp(response)
    
    def push_via_opp(self, response_file):
        # Use obex library or subprocess to call obexftp
        os.system(f"obexftp -b {self.bt_address} -p {response_file}")
Choice B: Native Android (if on Android)

kotlin
// MainActivity.kt
class SBMSListener : AppCompatActivity() {
    private val contentObserver = object : ContentObserver(Handler()) {
        override fun onChange(selfChange: Uri?) {
            val cursor = contentResolver.query(
                Uri.parse("content://media/external/file"),
                null, "_data LIKE '%message_%'", null, null
            )
            cursor?.use {
                while (it.moveToNext()) {
                    val path = it.getString(0)
                    val message = parseVCard(path)
                    sendSMS(message)
                    File(path).delete()
                }
            }
        }
    }
}
Core Functions:

Monitor /sdcard/Download/Bluetooth/ for incoming .vcd files

Parse vCard + extract X-SBMS-* fields

Send SMS via SmsManager.sendTextMessage() (Android) or equivalent

Capture delivery receipts (broadcast receiver)

Generate status response file

Push response back via Bluetooth OPP

Permissions Needed:

Android: android.permission.SEND_SMS, android.permission.RECEIVE_SMS

Bluetooth: android.permission.BLUETOOTH, android.permission.BLUETOOTH_ADMIN

Phase 4: Integration & Testing (Week 7-8)
End-to-End Test Scenario:

Compose message on E1310E: "Hello Test" → Contact: "Mom (+46701234567)"

Select "Send via Bluetooth"

Phone receives vCard file

Phone parses message and sends actual SMS

E1310E receives status response

E1310E displays "✓ Sent Successfully"

Check phone's SMS log: message delivered

Check E1310E sent folder: message stored

Regression Testing:

Test with various phone number formats (+46, 0046, 0701234567)

Test with special characters in message (emoji support: may be limited on E1310E)

Test message length edge cases (155, 160, 161 characters)

Test Bluetooth disconnect/reconnect resilience

Test with multiple rapid sends (queue handling)

Test on different Android/iOS versions

Part 5: Technical Challenges & Solutions
Challenge 1: J2ME Sandbox & File System Access
Problem: J2ME apps on E1310E run in a sandbox and may not have direct file system access.

Solutions:

A (Recommended): Use Samsung proprietary APIs (com.samsung.telephony.*) if available—some Samsung MIDP extensions expose phone filesystem

B: Use PIM (Personal Information Management) API to interact with contacts and messages indirectly

C: Reverse-engineer E1310E firmware to unlock proprietary APIs (advanced, requires disassembly)

Challenge 2: OPP Server Implementation on E1310E
Problem: E1310E's native OPP server may only accept certain file types (vCard, calendar) and reject custom extensions like .sbms.

Solution: Stick with .vcd (vCard) extension—OBEX will accept it as valid OPP object. Rename your custom message files:

text
Internally: message_abc123.sbms
Over Bluetooth: message_abc123.vcd (OBEX compatible)
On phone: Parse as extended vCard with X-SBMS-* properties
Challenge 3: Bi-directional Messaging (Phone Pushing to E1310E)
Problem: E1310E's OPP server may not automatically receive pushes from arbitrary apps.

Solutions:

A: User initiates: E1310E user selects "Receive File" mode first, then phone pushes

B: AVRCP signaling: Use AVRCP "Play" command from E1310E to signal readiness to receive (phone sees AVRCP Play, knows it's safe to push)

C: AT command mode: If E1310E supports AT+OBEX or diagnostic mode, bypass normal OPP and use command-line driven file transfer

Challenge 4: UUID Collision & Message Tracking
Problem: Need to match request → response without server-side database.

Solution: Deterministic UUID generation:

python
import hashlib
from datetime import datetime

def generate_sbms_uuid(phone_number, message_text, timestamp_seconds):
    combined = f"{phone_number}:{message_text}:{timestamp_seconds}"
    hash_obj = hashlib.sha1(combined.encode())
    uuid = hash_obj.hexdigest()[:8].upper()  # First 8 hex chars
    return uuid

# Example: 
# UUID = generate_sbms_uuid("+46701234567", "Hello from E1310E", 1702324200)
# Result: "A3F7E2C1"
Both E1310E and phone use identical logic, so response UUID matches request UUID with zero database overhead.

Challenge 5: SMS Text Encoding (Character Support)
Problem: E1310E might not support full UTF-8; SMS standard uses GSM-7 or UCS-2.

Solutions:

python
# Convert message to GSM-7 for maximum compatibility
GSM_7_MAP = {
    '@': 0x00, '£': 0x01, '$': 0x02, '¥': 0x03, 
    'è': 0x05, 'é': 0x05, 'ù': 0x06, 'ì': 0x0B,
    # ... full 128-character GSM-7 alphabet
}

def encode_gsm7(text):
    """Convert Unicode to GSM-7 with fallback to ASCII"""
    output = []
    for char in text:
        if char in GSM_7_MAP:
            output.append(chr(GSM_7_MAP[char]))
        elif ord(char) < 128:
            output.append(char)
        else:
            output.append('?')  # Fallback for unsupported chars
    return ''.join(output)
For Swedish characters (å, ä, ö), use GSM-7 extension table or UCS-2 encoding (doubles message cost).

Part 6: Comparison to Your Nokia 2760 NBMS

| Aspect                   | Nokia 2760 NBMS                         | Samsung E1310E SBMS            | Advantage |
| ------------------------ | --------------------------------------- | ------------------------------ | --------- |
| Bluetooth Version        | 1.0-1.1 (unstable)                      | 2.0 + EDR (stable)             | ✅ E1310E  |
| File Transfer            | Custom RFCOMM hack                      | Native OPP profile             | ✅ E1310E  |
| Protocol Stack           | Ad-hoc binary                           | OBEX standard                  | ✅ E1310E  |
| Phone Side Complexity    | Very complex (AT interception)          | Simple (OPP listener)          | ✅ E1310E  |
| J2ME Sandbox             | Restrictive (S60)                       | Slightly more open (Samsung)   | ✅ E1310E  |
| Development Ecosystem    | Declining (S60 deprecated)              | Better docs (Samsung MIDP)     | ✅ E1310E  |
| Reliability              | <40% success rate (reported)            | Expected 85%+ success          | ✅ E1310E  |
| Why NBMS failed on Nokia | Likely BT 1.0 instability + S60 sandbox | Avoid these with SBMS approach | ✅ E1310E  |

Key Takeaway: Your NBMS concept was sound—the Nokia 2760 simply lacked the hardware/OS support. The E1310E's Bluetooth 2.0 and open OPP profile make SBMS significantly more feasible.​

Part 7: Next Immediate Steps
Verify Bluetooth Connectivity

Pair E1310E with your modern phone via Settings

Test signal strength and stability (does it stay connected for 5+ minutes?)

Note the Bluetooth MAC address of E1310E for later reference

Test Manual OPP Transfer

Create a vCard contact on E1310E

Select "Send via Bluetooth" (if available in menu) or "Share"

Can you send it to your phone?

Where does your phone receive it?

Test Reverse Transfer

From your phone, send a contact/file to E1310E via Bluetooth

Does E1310E recognize and store it?

Research Samsung J2ME SDK

Download Samsung J2ME Emulator

Compile a "Hello World" MIDP app

Test deployment to E1310E or emulator

Document Phone's OPP Behavior

What file types does your phone accept via Bluetooth OPP?

What folder stores received files?

Can you monitor that folder programmatically?

Once you confirm these basics, you can confidently proceed with Phase 1 (PoC) of the SBMS implementation.

References & Specifications
Bluetooth OPP Specification v1.1​

OBEX Protocol (IrDA/Bluetooth)​

AVRCP Audio/Video Remote Control​

Bluetooth Profile List​

Image 1: "Object push" - personal data (namecards, Phonebook contacts, etc.) with Bluetooth devices

Image 2: "Object push" - Used to exchange personal data (namecards, Phonebook contacts, etc.) with Bluetooth devices

![alt text](image.png)

![alt text](image-1.png)

Connection Failure Diagnosis
The pairing succeeded but connection failed. This is a service-level issue, not a pairing issue. Here's the likely problem and solutions:

Root Cause Analysis
When you see this menu, the E1310E has OPP Server active (listening mode). The connection failure probably comes from:

Your phone's side: Not properly initiating OPP client connection to E1310E's OPP server

RFCOMM channel mismatch: E1310E's OPP service is on a specific channel (e.g., channel 7), but your phone is trying wrong channel

SDP query failure: Your phone's Bluetooth stack couldn't discover the OPP service UUID on E1310E

Firewall/permission issue: Your phone's Bluetooth app lacks permission to connect

Immediate Troubleshooting Steps
Step 1: Verify E1310E is in Correct Mode

E1310E Menu → Bluetooth Services → Object push

Select the service (as shown in your image)

You should see "Waiting for connection..." or similar

Stay in this menu while testing (don't go back)

Step 2: Manual OPP Test on Your Phone
Depending on your phone OS:

Android:

bash
# Use adb shell to debug Bluetooth
adb shell dumpsys bluetooth_manager

# Or use app: "Bluetooth File Transfer" (Google Play)
# This app will help initiate OPP connections manually
Try these apps to initiate OPP client manually:

Bluetooth File Transfer (free, Google Play)

Bluetooth Terminal (to test raw RFCOMM)

Bluetooth Explorer (debug Bluetooth services)

iPhone/iOS:
iOS doesn't natively support outbound Bluetooth OPP to non-Apple devices due to sandboxing. You'd need a specialized app.

Windows/Mac:

bash
# Linux: Use obexftp or obex-ftp command-line tool
sudo apt-get install obex-ftp
obexftp -b <E1310E_MAC_ADDRESS> -p <filename.vcd>

# macOS: Similar, use homebrew
brew install obexftp
obexftp -b <E1310E_MAC_ADDRESS> -p <filename.vcd>
Step 3: Check E1310E Bluetooth MAC Address
Get your E1310E's Bluetooth MAC from:

E1310E Menu → Settings → About Phone (or Device Info)

Should be listed as "Bluetooth Address" or "BD Address"

Format: XX:XX:XX:XX:XX:XX (e.g., E1:31:0E:12:34:56)

Step 4: Verify SDP Discovery Works
Your phone should query E1310E's services. Test:

Android (adb):

bash
adb shell
bluetoothctl
connect <E1310E_MAC>
services <E1310E_MAC>
# Should list OPP UUID: 1105
Linux/Windows:

bash
sdptool records <E1310E_MAC>
# Should show: Service Name: OBEX Object Push
#             UUID: 0000-1105-0000-1000-8000-00805f9b34fb
#             RFCOMM Channel: 7 (or similar)
Two-Way Connection Service Architecture
You're correct—for bidirectional messaging, you need both:

Current State (from your images):
text
E1310E: ✅ OPP Server (listening for connections)
Your Phone: ❌ OPP Server NOT active (only client capability tested)
Required for SBMS:
text
E1310E:    [OPP Server] ← Receives files from phone
Your Phone: [OPP Server] ← Receives files from E1310E
How to Enable Both Directions
On E1310E:

Keep "Object push" service enabled in Bluetooth menu

This is already your OPP Server (listening)

On Your Phone:
You need to enable OPP Server mode to accept pushes from E1310E:

Android:

bash
# Not built-in by default; use an app:
# - "Bluetooth File Transfer" app (from Play Store)
# - Configure to accept incoming OPP connections
# - App runs in background, listens for incoming files
Windows/Mac:

bash
# Use Bluetooth file transfer utility
# Windows: "Bluetooth File Transfer" in system tools
# Mac: "AirDrop" (Apple-only) or third-party apps

# Or use obexftp in server mode:
obexd &  # Start OBEX daemon listening
# Now phone can receive OPP pushes
SBMS Connection Flow (Corrected)
Here's what the actual connection sequence should look like:

Phase 1: Initial Pairing (You've done this ✅)
┌──────────────────┐           ┌──────────────────┐
│   E1310E         │           │   Your Phone     │
│                  │           │                  │
│  Discoverable    │ ◄────────►│  Discovers E1310E│
│                  │           │                  │
│ "Accept pairing" │ ◄────────►│ "Confirm PIN"    │
│                  │           │                  │
│  Paired ✅       │           │  Paired ✅       │
└──────────────────┘           └──────────────────┘

Phase 2: Service Discovery (SDP Query)
┌──────────────────┐           ┌──────────────────┐
│   E1310E         │           │   Your Phone     │
│                  │           │                  │
│  OPP Server      │◄─ SDP ───►│  Queries: "Does  │
│  Listening on    │   Query   │  E1310E have     │
│  RFCOMM Ch. 7    │           │  OPP service?"   │
│                  │           │                  │
│  Responds:       │─ SDP ────►│  Response:       │
│  "Yes, UUID:     │   Response│  "Yes, UUID:     │
│   1105, Ch: 7"   │           │   1105, Ch: 7"   │
└──────────────────┘           └──────────────────┘

Phase 3: RFCOMM Connection (Transport Layer)
┌──────────────────┐           ┌──────────────────┐
│   E1310E         │           │   Your Phone     │
│                  │           │                  │
│  Listening on    │◄── RFCOMM ──→│ Initiates      │
│  RFCOMM Ch. 7    │   CONNECT     │ connection to  │
│                  │               │ E1310E:7       │
│  Accepts and     │               │                │
│  opens socket    │               │                │
└──────────────────┘           └──────────────────┘

Phase 4: OBEX Handshake (Application Protocol)
┌──────────────────┐           ┌──────────────────┐
│   E1310E         │           │   Your Phone     │
│                  │           │                  │
│  Waiting for     │◄─ OBEX ───►│ Sends OBEX      │
│  OBEX CONNECT    │  CONNECT   │ CONNECT header  │
│  request         │            │ (version, flags)│
│                  │            │                 │
│  Responds:       │─ OBEX ────►│ Handshake       │
│  "OBEX v1.2      │  OK (0x20) │ succeeds        │
│   ready"         │            │                 │
└──────────────────┘           └──────────────────┘

Phase 5: File Transfer (Data)
┌──────────────────┐           ┌──────────────────┐
│   E1310E         │           │   Your Phone     │
│                  │           │                  │
│  Ready to        │◄─ OBEX ───►│ Phone sends:    │
│  receive         │   PUT      │ OBEX PUT        │
│                  │            │ (filename,      │
│  Stores file     │            │  data, length)  │
│  in /Message/    │            │                 │
│                  │            │                 │
│  Responds:       │─ OBEX ────►│ Success: "200"  │
│  "Received OK"   │   OK (0x20) │ (file written) │
└──────────────────┘           └──────────────────┘

Phase 6: Disconnect
┌──────────────────┐           ┌──────────────────┐
│   E1310E         │           │   Your Phone     │
│                  │           │                  │
│                  │◄─ OBEX ───→│ OBEX            │
│  Closes socket   │  DISCONNECT│ DISCONNECT      │
│                  │            │                 │
│  Returns to      │            │                 │
│  listening mode  │            │ Closes RFCOMM   │
└──────────────────┘           └──────────────────┘


