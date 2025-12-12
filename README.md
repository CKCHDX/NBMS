# SBMS - Samsung Bluetooth Message Service
## Architecture & Implementation Guide

---

## 📋 Project Overview

**SBMS** is a **distributed message relay system** that bridges three devices:
- **Samsung E1310E** (2003 J2ME phone) - Message client
- **Samsung Z Fold 6** (Android) - Contact sync + SMS relay
- **Windows Host** (Python) - Control center & relay server

All devices communicate via **Bluetooth** with the Windows host acting as the central hub.

---

## 🏗️ Architecture

### System Topology

```
                    Windows Host (Python)
                    ├─ Bluetooth Server
                    ├─ TCP Control Center
                    ├─ Contact Database
                    └─ Message Router
                         ↓ ↑
                    ┌────┴─────┐
                    ↓          ↓
            E1310E (J2ME)   Z Fold 6 (Python/Termux)
            ├─ Bluetooth    ├─ Bluetooth/TCP
            ├─ Message UI   ├─ Contact Sync
            └─ Send/Receive └─ SMS Relay
```

### Data Flow

#### 1. **Contact Synchronization**
```
Z Fold 6 → Windows Host → E1310E
(Reads contacts from device) → (Stores in JSON DB) → (Distributes to E1310E)
```

#### 2. **Message Sending**
```
E1310E User sends message
    ↓
E1310E app → Bluetooth → Windows Host
    ↓
Windows Host → TCP → Z Fold 6 (Termux Python)
    ↓
Z Fold 6 executes SMS via Shizuku
    ↓
Message sent to recipient
    ↓
Z Fold 6 → Windows Host → E1310E (Delivery status)
```

#### 3. **Real-time Synchronization**
```
Windows Control Center (UI) ← TCP ← Windows Host
    ↓
Displays:
  - Connected devices status
  - All contacts
  - Message history
  - Delivery status
```

---

## 🔧 Components

### 1. Windows Host (`sbms_windows_host.py`)

**Purpose**: Central relay server & contact database

**Features**:
- Bluetooth RFCOMM server (receives E1310E & Z Fold 6 connections)
- TCP server for local UI control center
- JSON-based contact database
- Message queuing & routing
- Connection state management
- Logging & monitoring

**Dependencies**:
```
python 3.8+
pybluez (pip install pybluez)
```

**Communication Protocol** (JSON over Bluetooth/TCP):

```json
// E1310E ping
{"type": "ping"}

// Z Fold 6 sync contacts
{"type": "sync_contacts", "contacts": [
  {"name": "Alice", "phone": "+46701234567"},
  {"name": "Bob", "phone": "+46702345678"}
]}

// E1310E request contacts
{"type": "get_contacts"}

// E1310E send message
{"type": "send_message", "to": "+46701234567", "text": "Hello", "id": "msg001"}

// Z Fold 6 delivery status
{"type": "sms_status", "id": "msg001", "status": "delivered"}
```

**Starting the Host**:
```bash
python sbms_windows_host.py
```

---

### 2. E1310E Client (`e1310e_sbms.jad` + `e1310e_sbms.jar`)

**Platform**: J2ME MIDP 2.0 / CLDC 1.1

**Purpose**: Message client for Samsung E1310E

**Features**:
- Bluetooth RFCOMM client connection
- Contact list display (retrieved from Windows)
- Message composition UI
- Send/receive messages via Windows relay
- Delivery status notifications
- Minimal memory footprint (<200KB)

**Building**:
```bash
cd SBMS-E1310E-app
set WTK_HOME=C:\WTK2.5.2
ant clean jar
```

**Output**: `dist/SBMS.jar`

**Deployment**:
```bash
obexftp -b E1:31:0E:XX:XX:XX -p dist/SBMS.jar
```

**J2ME Code Structure**:
```
src/
├─ com/oscyra/sbms/
│  ├─ SBMS.java (Main MIDlet)
│  ├─ ui/
│  │  ├─ ContactListScreen.java
│  │  ├─ MessageComposerScreen.java
│  │  └─ StatusScreen.java
│  └─ bluetooth/
│     └─ BluetoothManager.java
```

---

### 3. Z Fold 6 Client (`sbms_zfold6.py`)

**Platform**: Android + Termux (Python)

**Purpose**: Contact sync + SMS relay bridge

**Features**:
- Reads contacts from Z Fold 6 Android system
- Syncs contacts to Windows host
- Receives SMS send requests from Windows
- Uses Shizuku for privileged SMS access
- Maintains persistent TCP/Bluetooth connection
- Background service (systemd or Termux startup)

**Installation**:
```bash
# On Z Fold 6 in Termux
pkg install python android-api
pip install pybluez requests

# Copy script
cp sbms_zfold6.py $PREFIX/bin/sbms_zfold6
chmod +x $PREFIX/bin/sbms_zfold6

# Run in background
nohup sbms_zfold6 > sbms.log 2>&1 &
```

**Code Overview**:
```python
class ZFold6Client:
    def connect_to_windows(self):
        # Connect to Windows host via Bluetooth/TCP
        
    def sync_contacts(self):
        # Read contacts from Android ContactsProvider
        # Send to Windows host
        
    def listen_for_commands(self):
        # Wait for SMS send requests from Windows
        
    def send_sms_via_shizuku(self, to, text):
        # Use Shizuku to execute privileged SMS send
        # Report status back to Windows
        
    def maintain_connection(self):
        # Keep-alive pings, reconnect on failure
```

---

### 4. Windows Control Center UI

**Type**: PyQt6 desktop application (Windows 7/10)

**Purpose**: Management interface for Windows host

**Features**:
- Real-time device connection status
- Contact list view & search
- Compose & send messages
- Message history
- Delivery receipts
- Device management (pair new devices)

**Building**:
```bash
pip install PyQt6
python sbms_control_center.py
```

---

## 📱 Device Specifications

### Samsung E1310E
- **OS**: J2ME MIDP 2.0
- **Memory**: 10 MB
- **Bluetooth**: RFCOMM
- **Screen**: 96×65 pixels
- **Year**: 2003

### Samsung Z Fold 6
- **OS**: Android 14
- **Bluetooth**: BLE + Classic
- **Runtime**: Termux (Python 3.10+)
- **Features**: Shizuku support, ContactsProvider API

### Windows Host
- **OS**: Windows 7 / Windows 10+
- **Python**: 3.8+
- **Bluetooth**: USB adapter (CSR 4.0 recommended)
- **Role**: Central relay server

---

## 🔐 Security Considerations

### Current Implementation
- **Local network only** (Bluetooth + TCP on localhost)
- **No encryption** (suitable for LAN)
- **MAC address filtering** (E1310E & Z Fold 6 hardcoded)

### Production Hardening (Future)
- TLS/SSL encryption (Bluetooth + TCP)
- Token-based authentication
- Message signing
- Rate limiting
- Firewall rules

---

## 🚀 Getting Started

### Step 1: Prepare Windows Host

```bash
# Install Python 3.8+
# Download: https://www.python.org/downloads/

# Install Bluetooth library
pip install pybluez

# Clone repository
git clone https://github.com/CKCHDX/SBMS.git
cd SBMS
```

### Step 2: Pair Devices

**E1310E**:
```bash
# On Windows, use Bluetooth settings
# Pair E1310E manually
# Note MAC address: E1:31:0E:XX:XX:XX
```

**Z Fold 6**:
```bash
# On Z Fold 6, pair Windows via Bluetooth
# Note Windows Bluetooth MAC
# Install Termux
# Copy sbms_zfold6.py
```

### Step 3: Build & Deploy

**E1310E JAR**:
```bash
cd SBMS-E1310E-app
set WTK_HOME=C:\WTK2.5.2
ant clean jar
obexftp -b E1:31:0E:XX:XX:XX -p dist/SBMS.jar
```

**Z Fold 6 Script**:
```bash
# In Termux
pip install -r requirements.txt
python sbms_zfold6.py
```

**Windows Host**:
```bash
python sbms_windows_host.py
```

### Step 4: Verify Connections

All three should show:
```
Windows Host Log:
✓ Bluetooth server listening
✓ E1310E connected
✓ Z Fold 6 connected
✓ Contacts synced (N items)
```

---

## 📝 API Reference

### Bluetooth Message Protocol

#### Client → Host

```json
// Connection handshake
{
  "type": "identify",
  "device": "e1310e|zfold6",
  "version": "1.0"
}

// Keep-alive
{"type": "ping"}

// E1310E: Get contacts
{"type": "get_contacts"}

// E1310E: Send message
{
  "type": "send_message",
  "to": "+46701234567",
  "text": "Hello World",
  "id": "msg001"
}

// Z Fold 6: Sync contacts
{
  "type": "sync_contacts",
  "contacts": [
    {"name": "Alice", "phone": "+46701234567"},
    {"name": "Bob", "phone": "+46702345678"}
  ]
}

// Z Fold 6: SMS delivery status
{
  "type": "sms_status",
  "id": "msg001",
  "status": "delivered|failed",
  "timestamp": "2025-12-12T09:50:00"
}
```

#### Host → Client

```json
// Response
{
  "type": "contacts",
  "data": {
    "+46701234567": {"name": "Alice", "phone": "+46701234567"},
    "+46702345678": {"name": "Bob", "phone": "+46702345678"}
  }
}

// Command (Host → Z Fold 6)
{
  "type": "send_sms",
  "to": "+46701234567",
  "text": "Hello",
  "id": "msg001"
}

// Notification (Host → E1310E)
{
  "type": "contacts_updated",
  "contacts": {...}
}

// Status response
{"type": "ack", "status": "ok"}
```

---

## 📊 Database Schema

### `contacts.json`
```json
{
  "+46701234567": {
    "name": "Alice",
    "phone": "+46701234567",
    "added": "2025-12-12T09:50:00",
    "last_contact": "2025-12-12T10:15:00"
  },
  "+46702345678": {
    "name": "Bob",
    "phone": "+46702345678",
    "added": "2025-12-12T09:45:00",
    "last_contact": null
  }
}
```

### Message Log (SQLite, future)
```sql
CREATE TABLE messages (
  id TEXT PRIMARY KEY,
  from_device TEXT,  -- "e1310e" or "zfold6"
  to_number TEXT,
  text TEXT,
  status TEXT,  -- "pending", "sent", "delivered", "failed"
  timestamp DATETIME,
  retry_count INT DEFAULT 0
);
```

---

## 🐛 Troubleshooting

### E1310E won't connect
1. Verify MAC address in `sbms_windows_host.py`
2. Check Bluetooth pairing on Windows
3. Ensure Bluetooth adapter is enabled
4. Test with standard J2ME Bluetooth app first

### Z Fold 6 connection drops
1. Check Termux Python is running
2. Verify Shizuku permissions
3. Check network connectivity (TCP fallback)
4. Review `sbms.log` for errors

### Messages not sending
1. Verify Z Fold 6 has SMS permission
2. Check Windows host is receiving commands
3. Review delivery status in log
4. Test SMS manually first via Shizuku

### Windows host crashes
1. Check Python version (3.8+)
2. Verify `pybluez` is installed
3. Review logs in `sbms_host.log`
4. Restart Bluetooth service

---

## 📚 Project Structure

```
SBMS/
├── README.md (this file)
├── requirements.txt
├── sbms_windows_host.py
├── sbms_zfold6.py
├── sbms_control_center.py
│
├── SBMS-E1310E-app/
│  ├── build.xml
│  ├── build.properties
│  ├── src/com/oscyra/sbms/
│  │  ├── SBMS.java
│  │  ├── ui/
│  │  │  ├── ContactListScreen.java
│  │  │  ├── MessageComposerScreen.java
│  │  │  └─ StatusScreen.java
│  │  └─ bluetooth/
│  │     └─ BluetoothManager.java
│  ├── lib/
│  └── dist/
│     └─ SBMS.jar
│
└── .github/
   └── workflows/
      └─ e1310e-build.yml
```

---

## 🔄 Development Workflow

### Building E1310E
```bash
cd SBMS-E1310E-app
set WTK_HOME=C:\WTK2.5.2
ant clean jar
# Output: dist/SBMS.jar (~60KB)
```

### Testing Windows Host
```bash
python sbms_windows_host.py
# Logs to: sbms_host.log
```

### Testing Z Fold 6 Script
```bash
# In Termux
python sbms_zfold6.py --test
# Mock connections for development
```

---

## 📞 Contact & Support

**Project**: SBMS (Samsung Bluetooth Message Service)  
**Author**: Alex Jonsson  
**Repository**: https://github.com/CKCHDX/SBMS  
**Location**: Kista, Sweden  

---

## 📄 License

This project is provided as-is for educational and personal use.

---

**Last Updated**: December 12, 2025  
**Status**: Architecture & Initial Implementation
