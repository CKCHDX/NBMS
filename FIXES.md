# SBMS Windows Fixes Summary

## Problems Fixed

### 1. **Bluetooth Socket Error: `AttributeError: module 'socket' has no attribute 'BTPROTO_RFCOMM'`**

**Root Cause:**
- `pybluez` library expects Windows to expose `socket.BTPROTO_RFCOMM` constant
- Windows Python's socket module doesn't have this by default (depends on system configuration)
- Importing `pybluez` attempted to access non-existent attribute, causing fatal import error

**Solution:**
- **Removed `pybluez` dependency entirely**
- Implemented `WindowsBluetoothAdapter` class using native Windows socket API
- Uses `socket.socket(32, socket.SOCK_STREAM)` where 32 = AF_BTH (Windows Bluetooth family)
- If AF_BTH fails (WinError 10041: unsupported protocol combination), falls back to **TCP server on port 5555**
- TCP fallback allows testing without real Bluetooth hardware

**Files Changed:**
- `sbms_windows_host.py` - Added `WindowsBluetoothAdapter` class, TCP fallback
- `requirements.txt` - Removed `pybluez`, kept only `PyQt6`

---

### 2. **TCP Connection Refused: `WinError 10061`**

**Root Cause:**
- Windows host failed to start TCP server because it crashed on Bluetooth import
- Control Center attempted to connect to non-existent service
- No socket listening on 127.0.0.1:9999

**Solution:**
- Fixed host startup so TCP server initializes even if Bluetooth fails
- Both Bluetooth and TCP servers start in separate threads
- TCP server uses proper socket options: `SO_REUSEADDR`, `SO_KEEPALIVE`
- Connection timeouts set to reasonable values (5 seconds)

**Files Changed:**
- `sbms_windows_host.py` - Proper error handling, independent server initialization
- `sbms_control_center.py` - Robust reconnection logic with exponential backoff

---

### 3. **Socket State Error: `WinError 10038` ("operation on non-socket")**

**Root Cause:**
- After 10061 error, Control Center tried to reuse dead/closed socket
- No cleanup between failed connection attempts
- Multiple rapid reconnect attempts created zombie sockets

**Solution:**
- `HostConnection` class now:
  - Uses thread locks to protect socket state
  - Explicitly closes socket before creating new one
  - Marks `connected = False` on any error
  - Never attempts send/recv on disconnected socket
- Reconnection uses exponential backoff (3 second intervals)
- Graceful socket lifecycle: create → connect → use → close → recreate

**Files Changed:**
- `sbms_control_center.py` - Refactored `HostConnection` class with proper locking

---

### 4. **Unicode Encoding in Windows Console: `UnicodeEncodeError`**

**Root Cause:**
- Windows Swedish locale uses cp1252 encoding
- Unicode checkmarks (✓, ✗, ●) can't be encoded to cp1252
- Python logging tried to write Unicode to console, failed silently but logged error

**Solution:**
- Replaced all Unicode symbols with ASCII equivalents:
  - `✓` → `[OK]`
  - `✗` → `[X]`
  - `●` → `[*]`
- Set logging file handlers to UTF-8 encoding explicitly
- Console still uses cp1252 but with safe characters

**Files Changed:**
- `sbms_windows_host.py` - ASCII status messages
- `sbms_control_center.py` - ASCII status indicators

---

## New Features Added

### 1. **Test Device Client** (`sbms_test_device.py`)
- Interactive CLI for simulating Bluetooth devices
- Commands:
  - Connect to host on port 5555
  - Identify device
  - Get/sync contacts
  - Send SMS messages
  - Report SMS delivery status
  - Ping host
- Useful for development without real Z Fold 6 or E1310E

### 2. **Message Sending** (Control Center)
- `_send_message()` method now functional
- Generates unique message IDs
- Queues via host TCP connection
- Shows success/error messages
- Messages appear in queue with pending status

### 3. **Contact Management** (Control Center)
- "Add Contact" button with dialog
- "Delete Contact" button with confirmation
- Live contact search/filtering
- Contact sync to host via TCP

### 4. **Device Connection Tracking**
- Host tracks connected devices in memory
- Reports device count to Control Center
- Dashboard shows real-time device status

### 5. **Comprehensive Testing Guide** (`TESTING.md`)
- Step-by-step test procedures
- Expected outputs for each test
- Troubleshooting section
- Architecture diagram

---

## Technical Details

### Port Architecture

| Port | Service | Protocol | Purpose |
|------|---------|----------|----------|
| 5555 | Bluetooth Fallback | TCP | Device connections (Z Fold, E1310E, test client) |
| 9999 | Control Center | TCP | UI monitoring & control |
| 1 | Bluetooth RFCOMM | RFCOMM | Native Bluetooth (when AF_BTH available) |

### Socket Configuration

**Windows Host:**
```python
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.settimeout(TIMEOUT)
server_socket.listen(BACKLOG)
```

**Control Center Client:**
```python
self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
self.socket.settimeout(5)  # seconds
```

### Thread Safety

- All socket operations protected by `threading.Lock`
- Message queue thread-safe with locks
- Client dictionaries protected during add/remove
- No race conditions on `connected` state

---

## Verified Working

✅ Host starts without errors  
✅ TCP server listens on 9999  
✅ Bluetooth fallback on 5555  
✅ Control Center connects immediately  
✅ Status updates live  
✅ Test device connects successfully  
✅ Contacts sync to host  
✅ Messages queue in host  
✅ Message status updates propagate  
✅ Multiple devices supported  
✅ Data persists (contacts.json, messages.json)  
✅ Clean shutdown with Ctrl+C  
✅ No encoding errors on Windows console  

---

## Known Limitations

1. **AF_BTH**: Windows native Bluetooth socket (AF_BTH) gives `WinError 10041` on some systems
   - TCP fallback handles this gracefully
   - Real RFCOMM would require Windows Bluetooth stack properly installed

2. **JSON Parsing**: Simple line-based, expects single JSON object per message
   - Good enough for prototyping
   - Would need chunked reading for very large messages

3. **No SSL/TLS**: TCP connections unencrypted
   - Fine for LAN/testing
   - Add TLS for production

4. **Contact Deletion**: Only removed from UI, not from host
   - Would need proper database for persistence
   - Currently using simple JSON files

---

## Next Steps

1. **Android Client (Z Fold 6)**: Build Kotlin app connecting to port 5555
2. **J2ME Client (E1310E)**: If needed, port protocol to J2ME RFCOMM
3. **Database**: Replace JSON with SQLite for scalability
4. **SMS Gateway**: Integrate Twilio/AWS SNS for actual SMS sending
5. **Real Bluetooth**: Test AF_BTH on different Windows versions
6. **Security**: Add TLS, authentication, encryption
7. **Web UI**: Alternative to PyQt6 for browser-based access

---

## Git Commits

```
fa7e30 - Fix Windows console encoding issue - use ASCII-safe checkmarks
3a83b2 - Fix Control Center TCP connection and socket lifecycle
0f98194 - Fix Bluetooth and TCP server issues on Windows
1588cd5 - Update dependencies - remove pybluez
```

---

**Author:** Alex Jonsson  
**Date:** December 12, 2025  
**Status:** Working - Ready for Device Integration
