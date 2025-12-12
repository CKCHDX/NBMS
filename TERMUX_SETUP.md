# SBMS Z Fold 6 - Termux Setup Guide

## Overview

This guide covers installing and running the SBMS Z Fold 6 client on Samsung Z Fold 6 via Termux.

The Z Fold 6 client:
- Connects to Windows host via TCP (port 5555)
- Syncs Android contacts to Windows
- Receives SMS send requests from Windows
- Uses Shizuku for privileged SMS access
- Runs as background service

---

## Prerequisites

### On Windows Host
- Windows host running `sbms_windows_host.py` on the same network
- Network accessible (IP address known)
- Bluetooth fallback port 5555 open

### On Z Fold 6
- Samsung Z Fold 6 or compatible Android device
- Termux installed from F-Droid (NOT Google Play - outdated)
- USB debugging enabled (for easier file transfer)

---

## Step 1: Install Termux

### Option A: F-Droid (Recommended)

1. **Install F-Droid**
   - Download from https://f-droid.org/
   - Open APK and install

2. **Open F-Droid and search for "Termux"**
   - Select official Termux app
   - Tap "Install"
   - Launch when complete

### Option B: GitHub Release

1. Download from: https://github.com/termux/termux-app/releases
2. Install the APK directly
3. Grant all requested permissions

---

## Step 2: Initialize Termux

### First Boot

When Termux launches for the first time:
```
$ 
```

It initializes the Termux filesystem. Wait for completion.

### Update Package List

```bash
apt update
apt upgrade
```

---

## Step 3: Install Python

```bash
apt install python

# Verify installation
python --version
# Should show: Python 3.11+ or similar
```

### (Optional) Install Python Dev Tools

```bash
apt install python-dev
```

---

## Step 4: Setup SBMS Directory

```bash
# Create SBMS directory
mkdir -p ~/.sbms
cd ~/.sbms

# Verify
ls -la ~
# Should show ".sbms" directory
```

---

## Step 5: Transfer SBMS Files to Z Fold 6

### Option A: Via USB / ADB

**On Windows:**
```powershell
# Enable USB debugging on Z Fold 6 first
# Settings > Developer Options > USB Debugging

adb connect DEVICE_IP  # Or via USB cable
adb push sbms_zfold6.py /data/data/com.termux/files/home/.sbms/
```

### Option B: Via Git (if git installed in Termux)

**In Termux:**
```bash
cd ~/.sbms
git clone https://github.com/CKCHDX/SBMS.git
cp SBMS/sbms_zfold6.py .
```

### Option C: Manual Copy

1. Copy `sbms_zfold6.py` to Z Fold 6 via:
   - Cloud storage (Google Drive, Dropbox, etc.)
   - Email
   - File transfer app
   - Termux text editor

2. **In Termux:**
```bash
# Verify file is present
ls -la ~/.sbms/
# Should show: sbms_zfold6.py
```

---

## Step 6: Configure Windows Host IP

### Get Windows Host IP Address

**On Windows (PowerShell):**
```powershell
ipconfig /all
# Look for "IPv4 Address" on your network adapter
# Example: 192.168.1.100
```

### Update Z Fold 6 Client

**In Termux:**
```bash
cd ~/.sbms
nano sbms_zfold6.py

# Find this line (around line 30):
DEFAULT_WINDOWS_HOST = "127.0.0.1"

# Change to your Windows IP:
DEFAULT_WINDOWS_HOST = "192.168.1.100"  # Example

# Save (Ctrl+O, Enter, Ctrl+X)
```

---

## Step 7: Test Connection

### Test Mode (No Persistent Connection)

**In Termux:**
```bash
cd ~/.sbms
python sbms_zfold6.py --host 192.168.1.100 --test
```

**Expected Output:**
```
2025-12-12 18:50:43,305 - INFO - Running in TEST MODE
2025-12-12 18:50:43,305 - INFO - Would connect to 192.168.1.100:5555
2025-12-12 18:50:43,305 - INFO - Testing contact retrieval...
2025-12-12 18:50:43,306 - INFO -   - Alice Andersson: +46701234567
2025-12-12 18:50:43,306 - INFO -   - Bob Bergstrom: +46702345678
2025-12-12 18:50:43,306 - INFO -   - Charlie Carlson: +46703456789
2025-12-12 18:50:43,307 - INFO - Testing SMS sending...
2025-12-12 18:50:43,307 - INFO - [MOCK SMS] To: +46701234567
2025-12-12 18:50:43,307 - INFO - Test mode complete
```

### Network Connectivity Check

**In Termux:**
```bash
# Test if you can reach Windows host
ping 192.168.1.100
# Should show responses from Windows

# Test if port 5555 is open
nc -zv 192.168.1.100 5555
# Should show "succeeded" or "open"
```

---

## Step 8: Run Z Fold 6 Client

### Start Service

**In Termux:**
```bash
cd ~/.sbms
python sbms_zfold6.py --host 192.168.1.100
```

**Expected Output:**
```
======================================================================
SBMS Z Fold 6 Client Started
======================================================================
Target: 192.168.1.100:5555
Device: Z Fold 6
======================================================================

Timers:
  - Reconnect: 5s
  - Ping: 10s
  - Sync: 30s

Press Ctrl+C to shutdown...

Connecting to 192.168.1.100:5555...
2025-12-12 18:50:43,305 - INFO - [OK] Connected to Windows host
2025-12-12 18:50:43,306 - INFO - Synced 3 contacts to host
```

### Keep Service Running

To keep the service running after closing Termux:

**Option A: Use `nohup`**
```bash
nohup python sbms_zfold6.py --host 192.168.1.100 > sbms.log 2>&1 &
echo $!  # Save this PID
```

**Option B: Use Termux Floating Terminal**

1. Hold power button to open quick settings
2. Tap floating terminal icon
3. Navigate to `~/.sbms`
4. Run the script
5. Minimize (doesn't kill the process)

**Option C: Termux Boot (Scheduled Start)**

1. Install "Termux:Boot" from F-Droid
2. Create `~/.termux/boot/sbms` with:
   ```bash
   #!/data/data/com.termux/files/usr/bin/sh
   python ~/.sbms/sbms_zfold6.py --host 192.168.1.100
   ```
3. Make executable: `chmod +x ~/.termux/boot/sbms`
4. Restart device - service auto-starts

---

## Step 9: Monitor the Service

### View Live Logs

**In Termux:**
```bash
tail -f ~/.sbms/zfold6.log
```

### Check if Running

**In another Termux session:**
```bash
ps aux | grep python

# Should show:
# user 12345 ... python sbms_zfold6.py --host 192.168.1.100
```

### Stop Service

**If running in foreground:**
```
Ctrl+C
```

**If running in background:**
```bash
pkill -f sbms_zfold6.py
```

---

## Step 10: Verify Integration with Windows Host

### Check Windows Host Logs

**On Windows (in PowerShell, where host is running):**
```
Look for log messages:
2025-12-12 18:50:43,305 - INFO - Device connection from ('192.168.1.X', XXXXX)
2025-12-12 18:50:43,306 - INFO - Device identified: Z Fold 6
2025-12-12 18:50:43,307 - INFO - Synced 3 contacts from device
```

### Check Control Center UI

**On Windows, run Control Center:**
```powershell
python sbms_control_center.py
```

**In Control Center:**
- Dashboard should show: "Devices: 1"
- Contacts tab should show 3 test contacts
- Devices tab should show Z Fold 6 as connected

---

## Configuration

### Edit Settings

**In `sbms_zfold6.py` (around line 20-26):**

```python
DEFAULT_WINDOWS_HOST = "127.0.0.1"   # Change to Windows IP
DEFAULT_WINDOWS_PORT = 5555         # Port (usually don't change)
DEVICE_NAME = "Z Fold 6"            # Customize device name

# Timers (in seconds)
RECONNECT_INTERVAL = 5              # Retry connection after 5s
PING_INTERVAL = 10                  # Keep-alive every 10s
SYNC_INTERVAL = 30                  # Sync contacts every 30s
```

---

## Troubleshooting

### "Connection refused (WinError 10061)"

**Problem:** Z Fold 6 can't reach Windows host

**Solutions:**
1. Check Windows host is running: `python sbms_windows_host.py`
2. Verify Windows IP address: `ipconfig`
3. Check devices on same network
4. Check Windows firewall:
   ```powershell
   # Allow port 5555
   netsh advfirewall firewall add rule name="SBMS" dir=in action=allow protocol=tcp localport=5555
   ```
5. Test connectivity: `ping WINDOWS_IP` from Termux

### "Connection timeout"

**Problem:** Connection hangs

**Solutions:**
1. Check network stability (Wi-Fi/mobile)
2. Restart both devices
3. Check port 5555 is not blocked: `nc -zv WINDOWS_IP 5555`

### "No contacts showing"

**Problem:** Contacts not syncing

**Solutions:**
1. Verify `get_contacts()` returns contacts
2. Check `~/.sbms/contacts_cache.json` exists
3. Run test mode: `python sbms_zfold6.py --test`
4. Check logs: `tail -f ~/.sbms/zfold6.log`

### "SMS not sending"

**Problem:** SMS send requests are received but not working

**Solutions:**
1. Verify Shizuku is installed and running
2. Grant Shizuku "Send SMS" permission in Android settings
3. Check logs for Shizuku errors: `tail -f ~/.sbms/zfold6.log`
4. In test mode, SMS is mocked - logs show `[MOCK SMS]` messages

### "Logs are huge"

**Problem:** Log files growing too large

**Solutions:**
```bash
# Clear old logs
rm ~/.sbms/zfold6.log

# Rotate logs
cd ~/.sbms
mv zfold6.log zfold6.log.$(date +%Y%m%d)
```

---

## Integration with Android SMS (Shizuku)

### Install Shizuku

1. Download Shizuku from: https://github.com/RikkaApps/Shizuku
2. Install the APK
3. Grant device admin permission
4. Start Shizuku service

### Grant SMS Permission to Python

**In Shizuku app:**
1. Open "Permissions"
2. Find Python / Termux
3. Grant "Send SMS" permission

### Test SMS Sending

**In Termux:**
```bash
cd ~/.sbms
python -c "from sbms_zfold6 import ShizukuSMS; ShizukuSMS.send_sms('+46701234567', 'Test')"
```

---

## Advanced: Autostart on Boot

### Create Boot Script

**In Termux:**
```bash
mkdir -p ~/.termux/boot
nano ~/.termux/boot/sbms
```

**Add:**
```bash
#!/data/data/com.termux/files/usr/bin/sh
cd ~/.sbms
python sbms_zfold6.py --host 192.168.1.100 > sbms.log 2>&1 &
```

**Save and make executable:**
```bash
chmod +x ~/.termux/boot/sbms
```

**Install Termux:Boot from F-Droid**
- App will auto-start scripts in boot directory on device startup

---

## File Structure

```
~/.sbms/
├── sbms_zfold6.py          # Main client script
├── zfold6.log              # Runtime logs
├── contacts_cache.json     # Cached contacts from last sync
└── sbms.log                # (Optional) nohup output
```

---

## Security Notes

### Current Implementation
- No encryption (development mode)
- Test contacts hardcoded
- SMS sending is mocked

### Production Recommendations
1. Use TLS encryption for TCP connection
2. Integrate real Android contact provider
3. Implement Shizuku SMS integration
4. Add authentication token
5. Restrict to local network only

---

## Next Steps

1. ✅ Z Fold 6 client running
2. ⏳ Build Android Java/Kotlin app for SMS integration
3. ⏳ Integrate real Shizuku SMS sending
4. ⏳ Build E1310E J2ME Bluetooth client
5. ⏳ End-to-end message testing

---

## Support

For issues:
1. Check `~/.sbms/zfold6.log` for errors
2. Run test mode: `python sbms_zfold6.py --test`
3. Verify Windows host is running
4. Check network connectivity: `ping WINDOWS_IP`

---

**Author:** Alex Jonsson  
**Date:** December 12, 2025  
**Status:** Ready for Z Fold 6 Integration
