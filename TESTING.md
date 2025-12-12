# SBMS Testing Guide

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                    SBMS Windows Host (9999)                      │
├──────────────────────┬──────────────────────────────────────────┤
│  TCP Control Center  │     Bluetooth Device Server (5555)       │
│  (127.0.0.1:9999)   │     (0.0.0.0:5555 TCP fallback)          │
│                      │                                          │
│  - Status reporting  │  - Z Fold 6 (Android)                    │
│  - Contact sync      │  - E1310E (J2ME)                         │
│  - Message queue     │  - Test devices                          │
└──────────────────────┴──────────────────────────────────────────┘
         ↑                            ↑
         │ TCP                        │ TCP/RFCOMM
         │                            │
   ┌─────┴────┐              ┌────────┴────────┐
   │ Control  │              │  Device Clients │
   │  Center  │              │ (Test device)   │
   └──────────┘              └─────────────────┘
```

## Setup

### Prerequisites

```powershell
# Activate virtual environment
(venv) C:\Users\akoj2\Desktop\oscyra.solutions\SBMS>

# Install dependencies (one-time)
pip install -r requirements.txt
```

## Test 1: Host Startup

**Terminal 1: Start the Windows Host**

```powershell
(venv) C:\Users\akoj2\Desktop\oscyra.solutions\SBMS> python sbms_windows_host.py
```

**Expected Output:**
```
2025-12-12 18:50:43,305 - INFO - Starting SBMS Windows Host
2025-12-12 18:50:43,307 - INFO - Bluetooth server started (TCP fallback on port 5555)
2025-12-12 18:50:43,815 - INFO - TCP server started on 127.0.0.1:9999
2025-12-12 18:50:44,328 - INFO - [OK] All services started successfully
```

**Success Criteria:**
- ✅ No errors
- ✅ TCP server listening on 9999
- ✅ Bluetooth fallback on 5555

## Test 2: Control Center Connection

**Terminal 2: Start the Control Center UI**

```powershell
(venv) C:\Users\akoj2\Desktop\oscyra.solutions\SBMS> python sbms_control_center.py
```

**Expected Behavior:**
- PyQt6 window opens
- Status bar shows `[OK] Connected` (green)
- Dashboard shows live statistics:
  - Contacts: 0
  - Messages: 0
  - Devices: 0

**Host Terminal Output:**
```
2025-12-12 18:51:12,576 - INFO - Control Center connection from ('127.0.0.1', 62022)
2025-12-12 18:51:12,577 - DEBUG - Control Center message: {'type': 'get_status'}
```

**Success Criteria:**
- ✅ UI connects without errors
- ✅ Status bar green
- ✅ Data refreshes every second

## Test 3: Test Device Client

**Terminal 3: Start the test device**

```powershell
(venv) C:\Users\akoj2\Desktop\oscyra.solutions\SBMS> python sbms_test_device.py
```

**Interactive Menu:**
```
============================================================
SBMS Test Device CLI
============================================================
1. Connect to host
2. Identify device
3. Get contacts
4. Sync contacts to host
5. Send SMS
6. Sync contacts to host
7. Send SMS
8. Report SMS status
9. Ping host
10. Disconnect
11. Exit
============================================================
```

### Test 3.1: Device Connection

**Test Device: Option 1 (Connect)**

```
Select option: 1
```

**Expected Output:**
```
[OK] Connected to 127.0.0.1:5555
[SEND] {'type': 'identify', 'device': 'Z Fold 6'}
[RECV] {'type': 'ack', 'status': 'identified'}
```

**Host Terminal:**
```
2025-12-12 18:51:12,576 - INFO - Device connection from ('127.0.0.1', 52134)
2025-12-12 18:51:12,577 - DEBUG - Device message: {'type': 'identify', 'device': 'Z Fold 6'}
2025-12-12 18:51:12,577 - INFO - Device identified: Z Fold 6
```

**Control Center:**
```
Status: 0 contacts, 0 messages
Devices: 1  # ← Updated!
```

### Test 3.2: Sync Contacts

**Test Device: Option 4 (Sync contacts)**

```
Select option: 4
```

**Expected Output:**
```
[INFO] Syncing 3 contacts...
  - Alice Andersson (+46701234567)
  - Bob Bergstrom (+46702345678)
  - Charlie Carlson (+46703456789)
[SEND] {'type': 'sync_contacts', 'contacts': [...]}
[RECV] {'type': 'ack', 'status': 'synced'}
```

**Control Center - Contacts Tab:**
- Should show 3 new contacts:
  - Alice Andersson | +46701234567 | 2025-12-12 | Never
  - Bob Bergstrom | +46702345678 | 2025-12-12 | Never
  - Charlie Carlson | +46703456789 | 2025-12-12 | Never

**Host Terminal:**
```
2025-12-12 18:51:12,577 - INFO - Synced 3 contacts from device
```

### Test 3.3: Send Message

**Test Device: Option 5 (Send SMS)**

```
Select option: 5
Enter recipient phone: +46701234567
Enter message text: Hello from test device!
```

**Expected Output:**
```
[SEND] {'type': 'send_message', 'id': 'msg_1702423872123', 'to': '+46701234567', 'text': 'Hello...'}
[RECV] {'type': 'ack', 'status': 'queued', 'id': 'msg_1702423872123'}
```

**Control Center - Messages Tab:**
- New message appears:
  - ID: msg_1702423872123
  - To: +46701234567
  - Text: Hello from test device!
  - Status: pending (yellow background)
  - Time: 2025-12-12 18:51:12

**Dashboard Update:**
```
Messages: 1  # ← Updated!
```

### Test 3.4: Report Status

**Test Device: Option 8 (Report SMS status)**

```
Select option: 8
Enter message ID: msg_1702423872123
Enter status (pending/delivered/failed): delivered
```

**Expected Output:**
```
[SEND] {'type': 'sms_status', 'id': 'msg_1702423872123', 'status': 'delivered'}
[RECV] {'type': 'ack', 'status': 'received'}
```

**Control Center - Messages Tab Update:**
- Status changes to: **delivered** (green background)

## Test 4: Control Center Message Sending

**Control Center UI - Messages Tab:**

1. **Add Contact (optional):**
   - Click "Add Contact" button
   - Name: "Test Contact"
   - Phone: "+46701234567"
   - Click "Add"

2. **Send Message:**
   - To: "+46701234567" (or use contact name)
   - Message: "Test message from Control Center"
   - Click "Send Message"

**Expected Output:**
```
[OK] Message queued to +46701234567: Test message from Cont...
```

**Control Center - Messages Tab:**
- New message appears with timestamp
- Status: pending (yellow)

**Host Terminal:**
```
2025-12-12 18:51:12,577 - INFO - Added message msg_xxx to +46701234567
```

## Test 5: Multiple Devices

**Terminal 4: Start second test device**

```powershell
(venv) C:\Users\akoj2\Desktop\oscyra.solutions\SBMS> python sbms_test_device.py
```

When prompted, connect (option 1)

**Control Center - Devices Counter:**
```
Devices: 2  # ← Both devices shown
```

## Test 6: Persistence

**Shutdown sequence:**

1. Test Device: Option 11 (Exit)
2. Control Center: Close window
3. Windows Host: Ctrl+C

**Check Files Created:**

```powershell
dir

# Should see:
# - contacts.json      (contact database)
# - messages.json      (message log)
# - sbms_host.log      (host logs)
# - control_center.log (UI logs)
```

**Restart and Verify:**

1. Start host
2. Start control center
3. Check that contacts and messages persist

## Common Issues

### "Connection refused (WinError 10061)"
- **Cause:** Host not running
- **Fix:** Start host in Terminal 1 first

### "Connection timeout"
- **Cause:** Host crashed or not listening
- **Fix:** Check host terminal for errors

### Unicode encoding errors (old code)
- **Cause:** Windows console cp1252 can't handle Unicode
- **Fix:** Already fixed - using ASCII characters

### No devices showing in Control Center
- **Cause:** Device not connecting to port 5555
- **Fix:** Ensure device connects successfully (option 1)

## Files

| File | Purpose |
|------|----------|
| `sbms_windows_host.py` | Main relay server (TCP + Bluetooth) |
| `sbms_control_center.py` | PyQt6 UI application |
| `sbms_test_device.py` | Interactive device simulator |
| `contacts.json` | Contact database |
| `messages.json` | Message queue log |
| `sbms_host.log` | Host debug logs |
| `control_center.log` | UI debug logs |

## Next Steps

1. **Real Bluetooth:** Replace TCP fallback with native Windows RFCOMM once AF_BTH works
2. **Android Client:** Build Kotlin app for Z Fold 6
3. **J2ME Client:** Port protocol to E1310E (if still needed)
4. **Message Persistence:** Add SQLite for larger message archives
5. **SMS Gateway:** Integrate with actual SMS provider (Twilio, AWS SNS, etc.)
