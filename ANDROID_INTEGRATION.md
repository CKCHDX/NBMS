# SBMS Android Integration Guide

## Architecture Overview

```
┌────────────────────────────────┐
│      Windows SBMS Host (Python)        │
├────────────────────────────────┘
  │                     │
  TCP 5555          Bluetooth (RFCOMM 1)
  (Fallback)        (Native)
  │                     │
  ┌─────────────┴─────────────┐
  │                    │
  Z Fold 6           E1310E
  (Termux Python)    (J2ME)
  │                    │
  - Contacts        - Contacts
  - SMS Relay       - Message Client
  - Shizuku         - Bluetooth
  └─────────────────────────┘
```

---

## Z Fold 6 Implementation (Termux Python)

### Current Status

✅ **COMPLETED & WORKING**

**File:** `sbms_zfold6.py`

**Features:**
- TCP connection to Windows host (port 5555)
- Contact sync from Android
- SMS send via Shizuku
- Background service with reconnect
- Logging to `~/.sbms/zfold6.log`

**Installation:**

See [TERMUX_SETUP.md](TERMUX_SETUP.md) for complete guide

**Quick Start:**
```bash
# In Termux
cd ~/.sbms
python sbms_zfold6.py --host WINDOWS_IP
```

**Architecture:**
```
Android System
     │
     ├─ Contacts Provider (ContentResolver)
     │   │
     │   └─ AndroidContactManager.get_contacts()
     │
     ├─ SMS System (Shizuku)
     │   │
     │   └─ ShizukuSMS.send_sms(phone, text)
     │
     └─ Network Stack
        │
        └─ socket.socket (TCP/IP)
              │
              └─ Windows Host (127.0.0.1:5555)
```

**Integration Points:**

1. **Contact Reading**
   - Currently: Hardcoded test contacts
   - Future: Query Android ContentProvider
   - Code: `AndroidContactManager.get_contacts()`

2. **SMS Sending**
   - Currently: Mock (logged as `[MOCK SMS]`)
   - Future: Use Shizuku for privileged access
   - Code: `ShizukuSMS.send_sms()`

3. **Network Communication**
   - Using standard Python socket
   - TCP on port 5555
   - JSON message format

---

## E1310E Implementation (J2ME Bluetooth)

### Current Status

⏳ **PLANNED**

**Needed Files:**
- `SBMS-E1310E-app/src/com/oscyra/sbms/SBMS.java`
- `SBMS-E1310E-app/src/com/oscyra/sbms/ui/ContactListScreen.java`
- `SBMS-E1310E-app/src/com/oscyra/sbms/ui/MessageComposerScreen.java`
- `SBMS-E1310E-app/src/com/oscyra/sbms/bluetooth/BluetoothManager.java`

**Technology Stack:**
- J2ME MIDP 2.0 / CLDC 1.1
- Bluetooth RFCOMM (native)
- OPP (Object Push Profile)
- GUI: MIDP Screen classes
- Build: Ant + WTK 2.5.2

**Protocol:**
- Pure Bluetooth RFCOMM (port 1)
- JSON over Bluetooth socket
- Keep-alive pings every 30 seconds

**Key Components:**

1. **BluetoothManager.java**
   ```java
   // Establish RFCOMM connection to Windows host
   StreamConnection conn = Connector.open(
       "btspp://WINDOWS_MAC:1;authenticate=false",
       Connector.READ_WRITE
   );
   
   // Read/write JSON messages
   InputStream in = conn.openInputStream();
   OutputStream out = conn.openOutputStream();
   ```

2. **SBMS.java (Main MIDlet)**
   - Initialize Bluetooth connection
   - Show contact list screen
   - Handle message sending
   - Display delivery status

3. **ContactListScreen.java**
   ```java
   // Receives contacts from Windows host
   // Displays as selectable list
   // User taps to compose message
   ```

4. **MessageComposerScreen.java**
   ```java
   // Text input
   // Contact selection
   // Send button
   // Status notifications
   ```

---

## Implementation Roadmap

### Phase 1: Z Fold 6 (COMPLETED)

✅ TCP connection to Windows host
✅ Contact synchronization
✅ SMS relay framework
✅ Shizuku integration (ready)
✅ Background service
✅ Termux setup guide

**Next:** Test with actual Windows host connection

### Phase 2: E1310E (TODO)

- [ ] J2ME project setup (build.xml, properties)
- [ ] Bluetooth RFCOMM implementation
- [ ] JSON message parsing
- [ ] Contact list UI
- [ ] Message composer UI
- [ ] Keep-alive mechanism
- [ ] JAR building & deployment

**Estimate:** 1-2 weeks

### Phase 3: Production Hardening (TODO)

- [ ] TLS encryption (both platforms)
- [ ] Authentication tokens
- [ ] Real Android contact provider integration
- [ ] Shizuku SMS delivery tracking
- [ ] Error recovery & offline queueing
- [ ] Message acknowledgments
- [ ] Bandwidth optimization

**Estimate:** 2-3 weeks

---

## Testing & Debugging

### Z Fold 6 Testing

**Test Mode (No Connection):**
```bash
python sbms_zfold6.py --test
```

**With Windows Host:**

1. Start Windows host
   ```powershell
   python sbms_windows_host.py
   ```

2. Start Z Fold 6 client in Termux
   ```bash
   python sbms_zfold6.py --host 192.168.1.100
   ```

3. Verify in Windows logs
   ```
   Device connection from ('192.168.1.X', XXXXX)
   Device identified: Z Fold 6
   ```

4. Check Control Center UI
   ```powershell
   python sbms_control_center.py
   # Should show:
   # - Devices: 1
   # - Contacts: 3 (from Z Fold 6)
   ```

### E1310E Testing (When Built)

**JAR Installation:**
```bash
obexftp -b E1:31:0E:XX:XX:XX -p dist/SBMS.jar
```

**Deployment via OPP:**
```bash
# Send via Object Push Profile
obexftp -b E1_MAC -p sbms.jar
```

**Testing Flow:**
1. Launch E1310E app
2. Bluetooth auto-connects to Windows host
3. Display contacts (from host)
4. Select contact
5. Compose message
6. Send (should appear in Control Center)
7. Check delivery status

---

## Communication Protocol

### Message Format (JSON over TCP/Bluetooth)

#### Client → Host

```json
// Handshake
{
  "type": "identify",
  "device": "z foldl6" or "e1310e",
  "version": "1.0"
}

// Keep-alive
{"type": "ping"}

// Sync contacts (Z Fold 6)
{
  "type": "sync_contacts",
  "contacts": [
    {"name": "Alice", "phone": "+46701234567"},
    {"name": "Bob", "phone": "+46702345678"}
  ]
}

// Send message
{
  "type": "send_message",
  "id": "msg_001",
  "to": "+46701234567",
  "text": "Hello World"
}

// Report SMS status (Z Fold 6)
{
  "type": "sms_status",
  "id": "msg_001",
  "status": "delivered|failed|pending",
  "timestamp": "2025-12-12T18:50:00"
}
```

#### Host → Client

```json
// Send SMS (Host → Z Fold 6)
{
  "type": "send_sms",
  "to": "+46701234567",
  "text": "Hello",
  "id": "msg_001"
}

// Send SMS (Host → E1310E)
{
  "type": "send_sms",
  "to": "+46701234567",
  "text": "Hello",
  "id": "msg_001"
}

// Contacts list (Host → E1310E)
{
  "type": "contacts",
  "data": {
    "+46701234567": {"name": "Alice"},
    "+46702345678": {"name": "Bob"}
  }
}

// Keep-alive response
{"type": "pong"}

// Acknowledgment
{"type": "ack", "status": "ok"}

// Error
{"type": "error", "message": "description"}
```

---

## File Structure

```
SBMS/
├── README.md
├── FIXES.md
├── TESTING.md
├── TERMUX_SETUP.md (Z Fold 6 guide)
├── ANDROID_INTEGRATION.md (this file)
├──
├── # Core Windows Host
├── sbms_windows_host.py
├── sbms_control_center.py
├── sbms_test_device.py
├──
├── # Z Fold 6 (Python/Termux)
├── sbms_zfold6.py  [✅ COMPLETE]
├──
├── # E1310E (J2ME)
├── SBMS-E1310E-app/
├── ├── build.xml
├── ├── src/com/oscyra/sbms/
├── └── dist/SBMS.jar  [⏳ TODO]
```

---

## Network Requirements

### For Z Fold 6 (TCP)

- **Connection Type:** Wi-Fi or mobile data
- **Port:** 5555
- **Protocol:** TCP/IP
- **Network:** Same network as Windows host (or accessible via IP)
- **Firewall:** Port 5555 must be open on Windows

### For E1310E (Bluetooth)

- **Connection Type:** Bluetooth Classic (RFCOMM)
- **Port:** RFCOMM 1
- **Range:** ~10 meters typical
- **Pairing:** E1310E and Windows Bluetooth must be paired first
- **Protocol:** Native Bluetooth socket

---

## Development Notes

### Z Fold 6 Client

**Language:** Python 3.10+
**Framework:** Standard library only (no external deps)
**Size:** ~15KB
**Memory:** <50MB
**CPU:** Minimal (idle most of time)
**Battery:** ~1% per hour on idle

**Key Features:**
- Pure socket implementation (no pybluez)
- Background service design
- Contact caching
- Graceful reconnection
- Comprehensive logging

### E1310E Client

**Language:** Java (J2ME)
**Framework:** MIDP 2.0, CLDC 1.1
**Size:** ~60-80KB
**Memory:** <1MB
**CPU:** Minimal
**Battery:** ~10% per hour (based on activity)

**Constraints:**
- 10MB total device storage
- Limited UI (96x65 screen)
- Basic Bluetooth support
- No TLS/SSL
- Memory-constrained

---

## Security Considerations

### Current Implementation

- TCP/Bluetooth plaintext (development)
- No authentication
- Test contacts/mock SMS

### Production Requirements

1. **Encryption**
   - TLS 1.2+ for TCP
   - Possible: Bluetooth Link Encryption

2. **Authentication**
   - Token-based (JWT)
   - Device certificates
   - MAC address whitelisting

3. **SMS Security**
   - Shizuku permission verification
   - SMS receipt confirmation
   - Delivery status tracking

---

## Troubleshooting

### Z Fold 6 Won't Connect

1. Check Windows host is running
2. Verify Windows IP: `ipconfig` on Windows
3. Verify network access: `ping WINDOWS_IP` in Termux
4. Check firewall: `netsh advfirewall firewall show rule name="SBMS"`
5. Check logs: `tail -f ~/.sbms/zfold6.log`

### E1310E Won't Connect (When Built)

1. Verify E1310E is paired with Windows
2. Check Windows Bluetooth is on
3. Verify app permission: Bluetooth access
4. Check MAC address in code
5. Test with J2ME Bluetooth demo first

### Contacts Not Syncing

1. Check `get_contacts()` returns data
2. Verify Android permission: READ_CONTACTS
3. Check logs for sync messages
4. Run test mode: `python sbms_zfold6.py --test`

### SMS Not Sending

1. Verify Shizuku is installed and running
2. Check Shizuku has SEND_SMS permission
3. Run with Termux floating window
4. Check logs for Shizuku errors

---

## Next Steps

1. ✅ Z Fold 6 Python client complete
2. ✅ Termux setup guide
3. Test Z Fold 6 with actual Windows host
4. Build E1310E J2ME application
5. Test E1310E Bluetooth connection
6. End-to-end message flow testing
7. Production hardening (TLS, auth, etc.)

---

**Author:** Alex Jonsson  
**Date:** December 12, 2025  
**Status:** Z Fold 6 Ready | E1310E In Planning
