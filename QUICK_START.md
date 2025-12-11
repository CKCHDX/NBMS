# SBMS Quick Start (5 Minutes)

## What is SBMS?

A Bluetooth messaging relay system that lets your Samsung E1310E (2009, no SIM) send SMS through your Samsung Z Fold 6.

## Get Running in 5 Minutes

### Step 1: Clone (1 min)
```bash
git clone https://github.com/CKCHDX/SBMS.git
cd SBMS && git checkout android-phase3
```

### Step 2: Build (2 min)
```bash
cd android
./gradlew installDebug
```

### Step 3: Pair Devices (1 min)
```
Z Fold 6: Settings → Bluetooth → Pair with E1310E
E1310E:   Accept pairing request
```

### Step 4: Start App (1 min)
```
1. Open SBMS app on Z Fold 6
2. Grant all permissions when prompted
3. Tap "Start Service"
4. Verify "✓ Running" status
```

**Done!** App is listening for Bluetooth messages.

---

## Test It Works

### E1310E → Z Fold 6

```
E1310E:
  Menu → Contacts
       → Select contact
       → Send via Bluetooth
       → Select Z Fold 6
       → Confirm

Z Fold 6:
  Check SBMS app → Should log "Message Received"
```

### View Logs

```bash
adb logcat -s SBMS* -v brief

# Expected:
SBMSBluetoothService: Received SBMS message: TO=+46..., TEXT=...
SBMSBluetoothService: SBMS message processed - Status: SENT
```

---

## Next Steps

### Want Full Details?

| Document | Purpose |
|----------|----------|
| [README.md](README.md) | Project overview & features |
| [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) | Technical details & architecture |
| [BUILD_AND_TEST.md](BUILD_AND_TEST.md) | Detailed testing procedures |
| [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md) | Timeline & phases |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | What was built & next steps |

### Next Phase

- **Phase 3.2**: Send responses back to E1310E
- **Phase 2**: Build J2ME app for E1310E UI
- **Phase 4**: End-to-end integration testing

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Build fails | Check Java 17+ installed: `java -version` |
| App won't install | Clear: `adb shell pm clear com.ckcdhx.sbms` |
| Files not detected | Find BT folder: `adb shell find /sdcard -name "*.vcd"` |
| SMS not sending | Verify SIM in Z Fold 6 & SEND_SMS permission |
| Bluetooth won't pair | Restart both devices, enable Bluetooth on both |

For more help, see [BUILD_AND_TEST.md](BUILD_AND_TEST.md) troubleshooting section.

---

**Ready to dive in? Clone the repo and start building!**

```bash
git clone https://github.com/CKCHDX/SBMS.git && cd SBMS
```
