# Samsung Bluetooth Message Service - E1310E Edition

## Overview

SBMS E1310E is a J2ME MIDP 2.0 application for the Samsung E1310E phone, enabling SMS messaging via Bluetooth connection to a paired modern phone (Z Fold 6).

## Features

- **J2ME MIDP 2.0 Compatible**: Runs on Samsung E1310E with minimal resources
- **Bluetooth OPP Support**: Communicates via Object Push Profile standard
- **Contact Integration**: Dynamically displays contacts synced from paired phone
- **Message Composition**: 160-character SMS message editor
- **Status Feedback**: Real-time delivery confirmations
- **Classic Samsung UI**: Familiar interface adapted to E1310E screen
- **Non-Touch Navigation**: Full D-Pad/numeric keypad support

## Architecture

```
src/com/oscyra/sbms/
├── SBMSApp.java              # MIDlet entry point
├── MainScreen.java           # Primary UI form
├── bluetooth/
│   └── BluetoothHandler.java    # OPP protocol handler
├── storage/
│   ├── StorageManager.java      # File I/O operations
│   ├── Contact.java             # Contact model
│   └── ContactManager.java      # Contact operations
└── ui/
    ├── MessageComposer.java     # vCard message formatting
    └── ContactSelector.java     # Contact picker UI
```

## Building

### Prerequisites

- **J2ME WTK 2.5.2+** (Wireless Toolkit)
  - Download: https://www.oracle.com/java/technologies/wtk-121-downloads.html
- **Samsung J2ME SDK** (Optional, for Samsung-specific APIs)
  - Download: Samsung Developer Program
- **Java 1.4 compiler** (CLDC/MIDP compatible)
- **Ant 1.9.0+** (Build automation)

### Quick Build

```bash
# Clone and switch branch
git clone https://github.com/CKCHDX/SBMS.git
cd SBMS
git checkout E1310E-app

# Build with Ant
ant jar

# Output: dist/SBMS.jar (~50-80 KB)
```

### Detailed Build Steps

1. **Set WTK path in build.xml**:
   ```bash
   # Edit build.xml
   <property name="wtk.home" value="/path/to/WTK2.5.2" />
   ```

2. **Compile Java sources**:
   ```bash
   ant compile
   ```

3. **Preverify bytecode** (required for J2ME):
   ```bash
   ant preverify
   ```

4. **Create JAR package**:
   ```bash
   ant jar
   ```

5. **Generate JAD file**:
   ```bash
   # Edit dist/SBMS.jad for deployment
   cat > dist/SBMS.jad << EOF
   MIDlet-1: SBMS, , com.oscyra.sbms.SBMSApp
   MIDlet-Jar-Size: 65536
   MIDlet-Jar-URL: SBMS.jar
   MIDlet-Name: Samsung Bluetooth Message Service
   MIDlet-Vendor: Oscyra Solutions
   MIDlet-Version: 1.0.0
   MicroEdition-Configuration: CLDC-1.1
   MicroEdition-Profile: MIDP-2.0
   EOF
   ```

### Installation

#### Via Bluetooth OPP

1. From paired phone, send SBMS.jar via Bluetooth
2. E1310E receives file in Messages/Inbox
3. E1310E automatically detects .jar and prompts installation
4. Confirm installation

#### Via USB (if supported)

1. Connect E1310E via USB to PC
2. Copy SBMS.jar to phone memory
3. Use phone menu: Applications → Install New App
4. Select SBMS.jar

#### Via Application Manager

1. Ensure JAD file accessible via HTTP
2. Phone menu: Applications → Download App
3. Enter JAD URL
4. Download and install

## Configuration

### Paired Phone MAC Address

Edit `ContactManager.java` and update phone device detection:

```java
private void loadStoredContacts() {
    // Phone MAC address for connection
    String phoneMAC = "001D7E80A0B8"; // Update with your phone's MAC
}
```

### Samsung-Specific APIs

To access Samsung phone's native services:

```java
import com.samsung.telephony.TelephonyManager;
import com.samsung.io.FileIO;

// Access Samsung extensions
TelephonyManager tm = TelephonyManager.getInstance();
```

## Permissions

J2ME MIDP 2.0 has built-in sandbox; only request necessary:

```xml
<!-- In SBMS.jad -->
MIDlet-Permissions: javax.microedition.io.Connector.comm
MIDlet-Permissions: javax.microedition.io.Connector.file
```

## Usage

### Basic Workflow

1. **Launch App**
   - E1310E Applications menu → SBMS

2. **Search Contact**
   - Type in "Find Contact" field
   - Filtered list updates dynamically
   - Select with D-Pad + OK

3. **Compose Message**
   - Selected contact appears in "To:" field
   - Type message (max 160 chars)
   - Character counter shows real-time count

4. **Send via Bluetooth**
   - Press "Send" button (numeric keypad 5 or OK)
   - Status shows "Sending..."
   - Phone confirms delivery via Bluetooth
   - Status updates to "✓ Sent" or "✗ Failed"

5. **View History**
   - Menu → Message History
   - Browse sent/received messages
   - View delivery status

### Navigation

**Without Touch Screen**:
- **D-Pad Up/Down**: Navigate menu items
- **D-Pad Left/Right**: Scroll text fields
- **OK/Center**: Select item or activate button
- **Numeric Keys 0-9**: Enter text (T9 input if supported)
- **Star (*) / Hash (#)**: Navigation shortcuts
- **End Key**: Go back/exit

**Physical Buttons**:
- **Soft Keys**: Context-sensitive ("Select", "Back", "Exit")
- **Navigation Pad**: D-Pad directional input

## Message Format

Messages are transmitted as vCard 2.1 with SBMS extensions:

```
BEGIN:VCARD
VERSION:2.1
PRODID:-//SBMS//1.0//EN
X-SBMS-MSG:true
X-SBMS-TO:+46701234567
X-SBMS-TEXT:Hello from E1310E
X-SBMS-PRIORITY:1
X-SBMS-TIMESTAMP:20251212T150000Z
X-SBMS-UUID:A3F7E2C1
END:VCARD
```

**Transmission Process**:
1. E1310E serializes message as vCard
2. Saves to /Message/ directory as message_UUID.vcd
3. Initiates Bluetooth OPP PUSH to paired phone
4. Phone receives and parses vCard
5. Phone sends native SMS via cellular network
6. Phone sends status response vCard back to E1310E
7. E1310E displays confirmation and moves message to /Sent/

## Troubleshooting

### Bluetooth Connection Failed

**Error**: "Connection failed - Error XXX"

**Causes & Solutions**:
- Phone not paired: Pair via E1310E Settings → Bluetooth
- Phone MAC incorrect: Update in ContactManager.java
- Phone OPP not enabled: Enable on phone Bluetooth settings
- Range too far: Move devices within 10m
- Interference: Move away from microwave, WiFi

**Debug**:
```java
// Add to BluetoothHandler.java for detailed logs
System.err.println("BT Error: " + exception.getMessage());
```

### Message Not Sending

**Symptom**: "Sending..." status freezes or shows "Failed"

**Causes**:
- Bluetooth disconnected: Reconnect
- Phone not listening: Restart phone SBMS app
- Message format invalid: Check vCard syntax
- No storage space: Clear old messages

### Storage Full

**Error**: "Cannot save message - Storage full"

**Solution**:
1. E1310E Menu → Tools → Memory/Storage
2. Delete old message files:
   - Menu → Message History → Sent
   - Select old messages, press Delete
3. Clear app cache:
   - Menu → Tools → Java Heap
   - Confirm garbage collection

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| App Launch | 2-3s | First load, contact list loading |
| Bluetooth Connect | 3-5s | Pairing assumed, RFCOMM setup |
| Message Send | 1-2s | vCard serialization + OPP transfer |
| Status Receive | 2-3s | Phone processes SMS + response |
| **Total Round Trip** | **8-13s** | E1310E → Phone → SMS → E1310E |

**Memory Usage**:
- App JAR: ~60 KB
- Runtime heap: ~200 KB
- Contact list (20 contacts): ~5 KB
- Message history (50 messages): ~20 KB

## Testing Checklist

- [ ] App installs without errors
- [ ] Menu navigation works via D-Pad
- [ ] Contacts load and display correctly
- [ ] Contact search filters accurately
- [ ] Message composition accepts 160 characters
- [ ] Character counter updates in real-time
- [ ] Bluetooth connection establishes
- [ ] Message sends without timeout
- [ ] Status response received from phone
- [ ] Sent message appears in history
- [ ] App doesn't crash on navigation
- [ ] Memory doesn't leak over time
- [ ] Battery drains at normal rate

## Known Limitations

1. **No SIM SMS**: E1310E has no SIM; must relay via Bluetooth
2. **No WiFi**: Uses Bluetooth only, no IP connectivity
3. **Screen Size**: 128x128 or 176x220 limits UI complexity
4. **Memory**: ~200 KB heap requires efficient data structures
5. **Keyboard**: No QWERTY; T9 or numeric input only
6. **No Multimedia**: Text SMS only; no MMS or pictures
7. **Single Connection**: Can only maintain one Bluetooth link

## Security Considerations

- Messages transmitted in clear vCard format (no encryption)
- Bluetooth connection uses phone's pairing security
- No authentication token between devices
- Phone number sent in plaintext

**Recommendations**:
- Only pair with trusted devices
- Use phone's Bluetooth security settings
- Don't share sensitive information
- For production: Implement vCard encryption

## Future Enhancements

- [ ] Bluetooth auto-reconnect on disconnect
- [ ] SMS delivery receipts integration
- [ ] Multi-part messages (>160 chars)
- [ ] Message templates
- [ ] Favorites/quick contacts
- [ ] Message encryption (AES)
- [ ] Contact sync from phone via PBAP
- [ ] Voice message support
- [ ] Scheduled messages
- [ ] Message filters and search

## License

MIT License - See LICENSE file

## Support

- GitHub Issues: https://github.com/CKCHDX/SBMS/issues
- Email: alex@oscyra.solutions
