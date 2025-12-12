# SBMS Windows Quick Start Guide

## Prerequisites

- Python 3.8+
- Windows 7 or later
- Virtual environment set up

## Installation

```powershell
# Navigate to SBMS directory
cd C:\Users\akoj2\Desktop\oscyra.solutions\SBMS

# Create virtual environment (if not already done)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

## Running the System

### Terminal 1: Start Windows Host

```powershell
(venv) PS C:\Users\akoj2\Desktop\oscyra.solutions\SBMS> python sbms_windows_host.py
```

**Expected output:**
```
2025-12-12 18:50:43,307 - INFO - Bluetooth server started (TCP fallback on port 5555)
2025-12-12 18:50:43,815 - INFO - TCP server started on 127.0.0.1:9999
2025-12-12 18:50:44,328 - INFO - [OK] All services started successfully
2025-12-12 18:50:44,328 - INFO - [OK] Bluetooth server listening
2025-12-12 18:50:44,328 - INFO - [OK] TCP server listening on 127.0.0.1:9999
2025-12-12 18:50:44,328 - INFO - [OK] Contact database ready
2025-12-12 18:50:44,328 - INFO - [OK] Message queue active

Press Ctrl+C to shut down...
```

### Terminal 2: Start Control Center UI

```powershell
(venv) PS C:\Users\akoj2\Desktop\oscyra.solutions\SBMS> python sbms_control_center.py
```

**Expected behavior:**
- PyQt6 window opens
- Status bar shows "[OK] Connected" in green
- Dashboard displays live stats:
  - Contacts: 0
  - Messages: 0
  - Devices: 0
  - Last update: timestamp

## Server Details

| Service | Address | Purpose |
|---------|---------|----------|
| **TCP Control Center** | 127.0.0.1:9999 | Communication with UI (Control Center) |
| **Bluetooth Fallback** | 0.0.0.0:5555 | Device connections (Z Fold, E1310E) - TCP fallback for testing |

## Architecture

```
┌─────────────────┐
│   Z Fold 6      │
│   E1310E        │  ──┐
│  (Devices)      │    │
└─────────────────┘    │
                       ├──> Port 5555 (TCP Fallback)
                       │    for Bluetooth
                       │
┌──────────────────────┴────┐
│   SBMS Windows Host       │
│   - Contact Database      │
│   - Message Queue         │
│   - Two Servers:          │
│     • TCP (9999)          │
│     • Bluetooth (5555)    │
└──────────────────────┬────┘
                       │
                       └──> Port 9999 (TCP)
                            to Control Center UI
┌─────────────────┐
│  Control Center │
│  PyQt6 UI       │
└─────────────────┘
```

## Log Files

- `sbms_host.log` - Windows host logs
- `control_center.log` - Control center UI logs
- `contacts.json` - Contact database
- `messages.json` - Message queue log

## Troubleshooting

### Control Center shows "Disconnected"
- Ensure Windows host is running (Terminal 1)
- Check if port 9999 is not blocked by firewall
- Check `control_center.log` for connection errors

### Windows host crashes on startup
- Ensure PyQt6 is NOT required for the host
- Only Control Center needs PyQt6
- Check `sbms_host.log` for detailed errors

### Bluetooth socket fails (WinError 10041)
- This is expected on Windows - system falls back to TCP on port 5555
- Native Windows Bluetooth support requires AF_BTH driver support
- TCP fallback is fully functional for testing

## Next Steps

1. **Create test device client** - Connect to port 5555 to simulate Z Fold or E1310E
2. **Wire up message sending** - Implement send_message in control center
3. **Add contact management** - Sync contacts between devices
4. **Implement SMS gateway** - Forward messages to actual SMS service

## Development Notes

- Host: Pure TCP sockets (no external Bluetooth library dependencies)
- Control Center: PyQt6 with threaded network worker
- Protocol: JSON-based message exchange
- No browser storage, all state in JSON files
- Thread-safe with locks on socket operations
