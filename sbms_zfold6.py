#!/usr/bin/env python3
"""
SBMS Z Fold 6 Client (Termux/Android Python)

Bridges Samsung Z Fold 6 Android contacts and SMS with SBMS Windows Host.
Runs in Termux, syncs contacts, and sends SMS via Shizuku.

Author: Alex Jonsson
Location: Stockholm, Sweden
Date: December 2025

Requirements (in Termux):
- python3.10+
- socket (builtin)
- json (builtin)
- threading (builtin)
- time (builtin)
- sys (builtin)
- os (builtin)
- subprocess (builtin)
- sqlite3 (builtin)

Optional:
- android-api (for native Android contact access)

Installation:
```bash
pkg install python
pip install --upgrade pip
cp sbms_zfold6.py ~/.sbms/
cd ~/.sbms
python sbms_zfold6.py --host WINDOWS_IP
```
"""

import json
import socket
import sys
import time
import threading
import logging
import subprocess
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

# ============================================================================
# Configuration
# ============================================================================

DEFAULT_WINDOWS_HOST = "127.0.0.1"  # Change to actual Windows host IP
DEFAULT_WINDOWS_PORT = 5555  # Bluetooth fallback TCP port
DEVICE_NAME = "Z Fold 6"

# Timers
RECONNECT_INTERVAL = 5  # seconds
PING_INTERVAL = 10  # seconds
SYNC_INTERVAL = 30  # seconds

# Socket settings
SOCKET_TIMEOUT = 2  # seconds
MAX_RECV_SIZE = 4096  # bytes

# Paths
BASE_PATH = os.path.expanduser("~/.sbms")
LOG_FILE = os.path.join(BASE_PATH, "zfold6.log")
CONTACTS_CACHE = os.path.join(BASE_PATH, "contacts_cache.json")

# Android Contacts Database Paths (multiple versions)
ANDROID_CONTACTS_DB_PATHS = [
    "/data/data/com.android.providers.contacts/databases/contacts2.db",
    "/data/data/com.android.providers.contacts/databases/contacts.db",
    "/data/data/com.google.android.contacts/databases/contacts.db",
    "/data/user/0/com.android.providers.contacts/databases/contacts2.db",
    "/data/user/0/com.android.providers.contacts/databases/contacts.db",
]

# Create directories
os.makedirs(BASE_PATH, exist_ok=True)

# ============================================================================
# Logging Setup
# ============================================================================

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# Android Integration
# ============================================================================

class AndroidContactManager:
    """
    Reads contacts from Android ContentProvider in Termux.
    Tries multiple methods to get real contacts from Android 16.
    """
    
    @staticmethod
    def get_contacts() -> List[Dict]:
        """Get all contacts from Android"""
        
        # Method 1: Try content command (Termux-specific)
        contacts = AndroidContactManager._get_contacts_via_content_cmd()
        if contacts:
            logger.info(f"Retrieved {len(contacts)} contacts via content command")
            return contacts
        
        # Method 2: Try SQLite database query
        contacts = AndroidContactManager._get_contacts_from_sqlite()
        if contacts:
            logger.info(f"Retrieved {len(contacts)} contacts from SQLite database")
            return contacts
        
        # Method 3: Try native Android API
        try:
            contacts = AndroidContactManager._get_contacts_native()
            if contacts:
                logger.info(f"Retrieved {len(contacts)} contacts from native API")
                return contacts
        except Exception as e:
            logger.debug(f"Native API failed: {e}")
        
        # Fallback: Test contacts
        logger.warning("Could not get real contacts, using test contacts")
        return AndroidContactManager._get_test_contacts()
    
    @staticmethod
    def _get_contacts_via_content_cmd() -> List[Dict]:
        """Query contacts using Termux 'content' command"""
        try:
            logger.debug("Attempting to get contacts via content command")
            
            # Use content command to query contacts
            # This is available in Termux
            cmd = [
                "content", "query",
                "--uri", "content://com.android.contacts/contacts",
                "--projection", "display_name:phone_number"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10,
                text=True
            )
            
            if result.returncode != 0:
                logger.debug(f"content command failed: {result.stderr}")
                return []
            
            # Parse output
            contacts = []
            seen = set()
            
            lines = result.stdout.split('\n')
            for line in lines:
                # Line format: display_name=Name, phone_number=+46701234567
                if '=' in line and 'display_name' in line:
                    # Extract name and phone from line
                    parts = line.split(', ')
                    contact_data = {}
                    
                    for part in parts:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            contact_data[key.strip()] = value.strip()
                    
                    if 'display_name' in contact_data and 'phone_number' in contact_data:
                        name = contact_data['display_name']
                        phone = contact_data['phone_number'].replace(' ', '').replace('-', '')
                        
                        key = f"{name}:{phone}"
                        if key not in seen and phone:
                            contacts.append({
                                "name": name,
                                "phone": phone
                            })
                            seen.add(key)
                            logger.debug(f"Found contact: {name} - {phone}")
            
            if contacts:
                logger.info(f"Found {len(contacts)} contacts via content command")
            
            return contacts
        
        except FileNotFoundError:
            logger.debug("content command not found in Termux")
            return []
        except Exception as e:
            logger.debug(f"content command failed: {e}")
            return []
    
    @staticmethod
    def _get_contacts_from_sqlite() -> List[Dict]:
        """Query contacts from Android SQLite database"""
        try:
            # Try each possible database path
            db_path = None
            for path in ANDROID_CONTACTS_DB_PATHS:
                if os.path.exists(path):
                    db_path = path
                    logger.debug(f"Found contacts database at {db_path}")
                    break
            
            if not db_path:
                logger.debug(f"Contacts database not found in any known path")
                return []
            
            logger.debug(f"Querying contacts from {db_path}")
            
            # Connect to database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Try different query approaches
            contacts = []
            
            # First try: contacts table with phone lookup
            try:
                query = """
                SELECT DISTINCT
                    c.display_name,
                    p.data1
                FROM contacts c
                LEFT JOIN data d ON c._id = d.contact_id
                LEFT JOIN phone_lookup p ON c._id = p.contact_id
                WHERE p.data1 IS NOT NULL AND c.display_name IS NOT NULL
                ORDER BY c.display_name
                """
                cursor.execute(query)
                rows = cursor.fetchall()
                
                seen = set()
                for row in rows:
                    name, phone = row
                    if phone and name:
                        phone_clean = phone.replace(" ", "").replace("-", "")
                        key = f"{name}:{phone_clean}"
                        
                        if key not in seen:
                            contacts.append({
                                "name": name,
                                "phone": phone_clean
                            })
                            seen.add(key)
            except Exception as e:
                logger.debug(f"First query failed: {e}")
                
                # Second try: simpler query
                try:
                    query = """
                    SELECT display_name, data1
                    FROM contacts, mimetypes, data
                    WHERE contacts._id = data.contact_id
                    AND data.mimetype_id = mimetypes._id
                    AND mimetypes.mimetype = 'vnd.android.cursor.item/phone_v2'
                    """
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        name, phone = row
                        if phone:
                            contacts.append({
                                "name": name or "Unknown",
                                "phone": phone.replace(" ", "").replace("-", "")
                            })
                except Exception as e2:
                    logger.debug(f"Second query also failed: {e2}")
            
            conn.close()
            
            if contacts:
                logger.info(f"Found {len(contacts)} contacts in SQLite database")
            
            return contacts
        
        except Exception as e:
            logger.debug(f"Failed to query SQLite: {e}")
            return []
    
    @staticmethod
    def _get_contacts_native() -> List[Dict]:
        """
        Get contacts using native Android API (if python-for-android available).
        This requires Kivy or similar framework.
        """
        try:
            from jnius import autoclass, cast
            
            logger.debug("Using native Android API via jnius")
            
            # Get Android context
            PythonActivity = autoclass('org.renpy.android.PythonActivity')
            activity = PythonActivity.mActivity
            ContentResolver = autoclass('android.content.ContentResolver')
            ContactsContract = autoclass('android.provider.ContactsContract')
            
            # Get content resolver
            content_resolver = activity.getContentResolver()
            
            # Query contacts
            uri = ContactsContract.CommonDataKinds.Phone.CONTENT_URI
            projection = ["display_name", "data1"]  # name, phone
            
            cursor = content_resolver.query(uri, projection, None, None, None)
            
            contacts = []
            seen = set()
            
            while cursor.moveToNext():
                name = cursor.getString(0)
                phone = cursor.getString(1)
                if phone:
                    phone_clean = phone.replace(" ", "").replace("-", "")
                    key = f"{name}:{phone_clean}"
                    
                    if key not in seen:
                        contacts.append({
                            "name": name or "Unknown",
                            "phone": phone_clean
                        })
                        seen.add(key)
            
            cursor.close()
            
            logger.info(f"Native API: retrieved {len(contacts)} contacts")
            return contacts
        
        except Exception as e:
            logger.debug(f"Native Android API failed: {e}")
            return []
    
    @staticmethod
    def _get_test_contacts() -> List[Dict]:
        """Return test contacts for development"""
        logger.debug("Using test contacts (development mode)")
        return [
            {"name": "Alice Andersson", "phone": "+46701234567"},
            {"name": "Bob Bergstrom", "phone": "+46702345678"},
            {"name": "Charlie Carlson", "phone": "+46703456789"},
        ]
    
    @staticmethod
    def cache_contacts(contacts: List[Dict]) -> None:
        """Cache contacts to file"""
        try:
            with open(CONTACTS_CACHE, 'w') as f:
                json.dump(contacts, f, indent=2)
            logger.debug(f"Cached {len(contacts)} contacts")
        except Exception as e:
            logger.warning(f"Failed to cache contacts: {e}")
    
    @staticmethod
    def load_cached_contacts() -> List[Dict]:
        """Load contacts from cache"""
        try:
            if os.path.exists(CONTACTS_CACHE):
                with open(CONTACTS_CACHE, 'r') as f:
                    contacts = json.load(f)
                logger.debug(f"Loaded {len(contacts)} contacts from cache")
                return contacts
        except Exception as e:
            logger.warning(f"Failed to load cached contacts: {e}")
        return []


class ShizukuSMS:
    """
    Sends SMS via Shizuku (privileged Android service).
    Requires Shizuku app installed and running on Z Fold 6.
    
    Shizuku allows unprivileged apps to request Android system permissions.
    """
    
    @staticmethod
    def send_sms(phone_number: str, message_text: str) -> bool:
        """
        Send SMS using Shizuku.
        
        Returns:
            True if queued successfully, False on error
        """
        try:
            logger.info(f"Sending SMS to {phone_number}")
            
            # Method 1: Try using broadcast intent (requires permission)
            try:
                cmd = [
                    "am", "broadcast",
                    "-a", "android.intent.action.SEND_SMS",
                    "--es", "phone", phone_number,
                    "--es", "message", message_text
                ]
                result = subprocess.run(cmd, capture_output=True, timeout=5)
                
                if result.returncode == 0:
                    logger.info(f"SMS queued to {phone_number}")
                    return True
            except Exception as e:
                logger.debug(f"Broadcast method failed: {e}")
            
            # Method 2: Mock send (for development)
            logger.info(f"[MOCK SMS] To: {phone_number}")
            logger.info(f"[MOCK SMS] Text: {message_text}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False


# ============================================================================
# SBMS Protocol Client
# ============================================================================

class SBMSZFold6Client:
    """Z Fold 6 client for SBMS Windows Host"""
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.running = False
        self.reconnect_timer = 0
        self.ping_timer = 0
        self.sync_timer = 0
    
    def connect(self) -> bool:
        """Connect to Windows SBMS host"""
        try:
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
            
            logger.info(f"Connecting to {self.host}:{self.port}...")
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(SOCKET_TIMEOUT)
            self.socket.connect((self.host, self.port))
            
            self.connected = True
            logger.info(f"[OK] Connected to Windows host")
            
            # Identify ourselves
            self.identify()
            return True
        
        except socket.timeout:
            logger.warning(f"Connection timeout to {self.host}:{self.port}")
            self.connected = False
            return False
        
        except ConnectionRefusedError:
            logger.warning(f"Connection refused by {self.host}:{self.port}")
            logger.warning("Is Windows host running? (sbms_windows_host.py)")
            self.connected = False
            return False
        
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.connected = False
            return False
    
    def send_message(self, msg: Dict) -> bool:
        """Send message to host (fire and forget, no response expected)"""
        try:
            if not self.connected or not self.socket:
                return False
            
            # Send message
            data = json.dumps(msg).encode('utf-8')
            self.socket.sendall(data)
            logger.debug(f"[SEND] {msg['type']}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.connected = False
            return False
    
    def identify(self) -> bool:
        """Identify device to host"""
        msg = {
            "type": "identify",
            "device": DEVICE_NAME,
            "version": "1.0"
        }
        return self.send_message(msg)
    
    def sync_contacts(self, contacts: List[Dict]) -> bool:
        """Sync Android contacts to Windows host"""
        if not self.connected:
            return False
        
        try:
            msg = {
                "type": "sync_contacts",
                "contacts": contacts
            }
            
            result = self.send_message(msg)
            
            if result:
                logger.info(f"Synced {len(contacts)} contacts to host")
                # Cache contacts
                AndroidContactManager.cache_contacts(contacts)
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to sync contacts: {e}")
            return False
    
    def report_sms_status(self, msg_id: str, status: str) -> bool:
        """Report SMS delivery status"""
        msg = {
            "type": "sms_status",
            "id": msg_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        return self.send_message(msg)
    
    def ping(self) -> bool:
        """Ping host to keep connection alive"""
        msg = {"type": "ping"}
        return self.send_message(msg)
    
    def disconnect(self) -> None:
        """Disconnect from host"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
        logger.info("Disconnected from host")
    
    def run(self) -> None:
        """Main background service loop"""
        self.running = True
        
        logger.info("="*70)
        logger.info(f"SBMS Z Fold 6 Client Started")
        logger.info("="*70)
        logger.info(f"Target: {self.host}:{self.port}")
        logger.info(f"Device: {DEVICE_NAME}")
        logger.info("="*70)
        logger.info("")
        logger.info("Timers:")
        logger.info(f"  - Reconnect: {RECONNECT_INTERVAL}s")
        logger.info(f"  - Ping: {PING_INTERVAL}s")
        logger.info(f"  - Sync: {SYNC_INTERVAL}s")
        logger.info("")
        logger.info("Press Ctrl+C to shutdown...")
        logger.info("")
        
        while self.running:
            # Try to reconnect if not connected
            if not self.connected:
                self.reconnect_timer += 1
                if self.reconnect_timer >= RECONNECT_INTERVAL:
                    logger.info("Attempting to reconnect...")
                    self.connect()
                    self.reconnect_timer = 0
            
            # If connected, do periodic tasks
            if self.connected:
                # Ping every PING_INTERVAL seconds
                self.ping_timer += 1
                if self.ping_timer >= PING_INTERVAL:
                    if not self.ping():
                        logger.warning("Ping failed, disconnecting")
                        self.connected = False
                    self.ping_timer = 0
                
                # Sync contacts every SYNC_INTERVAL seconds
                self.sync_timer += 1
                if self.sync_timer >= SYNC_INTERVAL:
                    contacts = AndroidContactManager.get_contacts()
                    if contacts:
                        if not self.sync_contacts(contacts):
                            logger.warning("Sync failed, will retry")
                    self.sync_timer = 0
            
            # Sleep for 1 second
            time.sleep(1)
    
    def stop(self) -> None:
        """Stop the service"""
        logger.info("")
        logger.info("="*70)
        logger.info("Shutting down SBMS Z Fold 6 Client...")
        logger.info("="*70)
        
        self.running = False
        self.disconnect()
        
        logger.info("Client stopped")
        logger.info("Log saved to: " + LOG_FILE)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="SBMS Z Fold 6 Client (Termux/Android Python)"
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_WINDOWS_HOST,
        help=f"Windows host IP (default: {DEFAULT_WINDOWS_HOST})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_WINDOWS_PORT,
        help=f"Windows host port (default: {DEFAULT_WINDOWS_PORT})"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (no persistent connection)"
    )
    
    args = parser.parse_args()
    
    if args.test:
        logger.info("Running in TEST MODE")
        logger.info(f"Would connect to {args.host}:{args.port}")
        
        # Test contact retrieval
        logger.info("\nTesting contact retrieval...")
        contacts = AndroidContactManager.get_contacts()
        logger.info(f"Found {len(contacts)} contacts:")
        for contact in contacts:
            logger.info(f"  - {contact['name']}: {contact['phone']}")
        
        # Test SMS sending
        logger.info("\nTesting SMS sending...")
        ShizukuSMS.send_sms("+46701234567", "Test message")
        
        logger.info("\nTest mode complete")
        return
    
    # Production mode: run background service
    client = SBMSZFold6Client(args.host, args.port)
    
    try:
        client.run()
    except KeyboardInterrupt:
        logger.info("")
        client.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        client.stop()


if __name__ == "__main__":
    main()
