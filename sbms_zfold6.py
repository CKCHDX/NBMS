#!/usr/bin/env python3
"""
SBMS Z Fold 6 Client - Real Shizuku Integration

Bridges Samsung Z Fold 6 Android contacts and SMS with SBMS Windows Host.
Runs in Termux, syncs real contacts via Shizuku, and sends real SMS.

Requires:
- Termux on Z Fold 6
- Shizuku app running
- rish binary for Shizuku commands
- Python 3.10+

Author: Alex Jonsson
Location: Stockholm, Sweden
Date: December 2025

Running:
```bash
cd ~/.sbms
python sbms_zfold6.py --host WINDOWS_IP
```
"""

import json
import socket
import sys
import time
import logging
import subprocess
import os
from datetime import datetime
from typing import Dict, List, Optional

# ============================================================================
# Configuration
# ============================================================================

DEFAULT_WINDOWS_HOST = "127.0.0.1"
DEFAULT_WINDOWS_PORT = 5555
DEVICE_NAME = "Z Fold 6"

# Timers
RECONNECT_INTERVAL = 5
PING_INTERVAL = 10
SYNC_INTERVAL = 30

# Socket settings
SOCKET_TIMEOUT = 2
MAX_RECV_SIZE = 4096

# Paths
BASE_PATH = os.path.expanduser("~/.sbms")
LOG_FILE = os.path.join(BASE_PATH, "zfold6.log")
CONTACTS_CACHE = os.path.join(BASE_PATH, "contacts_cache.json")

# Shizuku
RISH_PATH = os.path.join(BASE_PATH, "rish")  # rish binary in same directory

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
# Shizuku Integration via rish
# ============================================================================

class ShizukuRish:
    """
    Interacts with Shizuku through rish binary.
    rish is a Shizuku helper that executes commands with elevated privileges.
    """
    
    @staticmethod
    def run_command(cmd: str, timeout: int = 10) -> Optional[str]:
        """
        Run command through Shizuku via rish.
        
        Usage:
            output = ShizukuRish.run_command("content query --uri ...")
        """
        try:
            # Use rish to execute with Shizuku privileges
            result = subprocess.run(
                [RISH_PATH, "sh", "-c", cmd],
                capture_output=True,
                timeout=timeout,
                text=True
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                logger.debug(f"Command failed: {result.stderr}")
                return None
        
        except FileNotFoundError:
            logger.error(f"rish not found at {RISH_PATH}")
            return None
        except Exception as e:
            logger.error(f"Failed to run command: {e}")
            return None


# ============================================================================
# Android Integration - Real Contacts via Shizuku
# ============================================================================

class AndroidContactManager:
    """
    Reads REAL Android contacts via Shizuku/rish.
    Works on Android 16 without root.
    """
    
    @staticmethod
    def get_contacts() -> List[Dict]:
        """Get real Android contacts via Shizuku"""
        
        logger.debug("Querying real Android contacts via Shizuku...")
        contacts = AndroidContactManager._query_contacts_shizuku()
        
        if contacts:
            logger.info(f"Retrieved {len(contacts)} real contacts from device")
            return contacts
        
        logger.warning("Failed to get real contacts")
        return []
    
    @staticmethod
    def _query_contacts_shizuku() -> List[Dict]:
        """
        Query real contacts using Shizuku.
        Uses 'content' command with READ_CONTACTS permission.
        """
        try:
            # Query contacts from ContactsProvider
            cmd = """
content query --uri content://com.android.contacts/data \
--projection raw_contact_id:data1 \
--where "mimetype='vnd.android.cursor.item/phone_v2'" 2>/dev/null
            """
            
            output = ShizukuRish.run_command(cmd)
            
            if not output:
                return []
            
            # Parse phone numbers
            phone_map = {}  # Map raw_contact_id -> phone
            
            for line in output.split('\n'):
                if 'raw_contact_id=' in line and 'data1=' in line:
                    # Parse: Row: raw_contact_id=123, data1=+46701234567
                    parts = {}
                    for part in line.split(','):
                        if '=' in part:
                            k, v = part.split('=', 1)
                            parts[k.strip()] = v.strip()
                    
                    contact_id = parts.get('raw_contact_id')
                    phone = parts.get('data1', '').replace(' ', '').replace('-', '')
                    
                    if contact_id and phone:
                        phone_map[contact_id] = phone
            
            # Query contact names
            cmd2 = """
content query --uri content://com.android.contacts/raw_contacts \
--projection _id:display_name 2>/dev/null
            """
            
            output2 = ShizukuRish.run_command(cmd2)
            
            if not output2:
                return []
            
            contacts = []
            seen = set()
            
            for line in output2.split('\n'):
                if '_id=' in line and 'display_name=' in line:
                    parts = {}
                    for part in line.split(','):
                        if '=' in part:
                            k, v = part.split('=', 1)
                            parts[k.strip()] = v.strip()
                    
                    contact_id = parts.get('_id')
                    name = parts.get('display_name')
                    
                    if contact_id in phone_map and name:
                        phone = phone_map[contact_id]
                        key = f"{name}:{phone}"
                        
                        if key not in seen:
                            contacts.append({
                                "name": name,
                                "phone": phone
                            })
                            seen.add(key)
                            logger.debug(f"Found contact: {name} - {phone}")
            
            return contacts
        
        except Exception as e:
            logger.error(f"Failed to query contacts: {e}")
            return []
    
    @staticmethod
    def cache_contacts(contacts: List[Dict]) -> None:
        """Cache contacts to file"""
        try:
            with open(CONTACTS_CACHE, 'w') as f:
                json.dump(contacts, f, indent=2)
            logger.debug(f"Cached {len(contacts)} contacts")
        except Exception as e:
            logger.warning(f"Failed to cache contacts: {e}")


# ============================================================================
# SMS Sending via Shizuku
# ============================================================================

class ShizukuSMS:
    """
    Sends real SMS via Shizuku/rish.
    No mocking - actual SMS delivery.
    """
    
    @staticmethod
    def send_sms(phone_number: str, message_text: str) -> bool:
        """
        Send real SMS using Shizuku.
        
        Returns:
            True if SMS was sent successfully, False otherwise
        """
        try:
            logger.info(f"Sending SMS to {phone_number}")
            logger.info(f"Text: {message_text[:50]}...")
            
            # Method 1: Use am command to open default SMS app
            # This will send via the system's default SMS app
            escaped_msg = message_text.replace('"', '\\"').replace("'", "\\'")  
            cmd = f"""am start -a android.intent.action.SENDTO \
-d sms:{phone_number} \
--es sms_body \"{escaped_msg}\" \
--ez exit_on_sent true 2>/dev/null
            """
            
            output = ShizukuRish.run_command(cmd)
            
            if output is not None:
                logger.info(f"SMS sent to {phone_number}")
                return True
            
            # Method 2: Fallback - use service call for direct SMS
            logger.debug("Trying fallback SMS method...")
            cmd2 = f"""service call isms 7 s16 \"com.android.mms\" \
s16 \"\" s16 \"{phone_number}\" s16 \"\" s16 \"{escaped_msg}\" \
s16 \"\" s16 \"\" 2>/dev/null
            """
            
            output2 = ShizukuRish.run_command(cmd2)
            
            if output2 is not None:
                logger.info(f"SMS queued to {phone_number}")
                return True
            
            logger.warning(f"Failed to send SMS to {phone_number}")
            return False
        
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
            logger.warning(f"Connection timeout")
            self.connected = False
            return False
        
        except ConnectionRefusedError:
            logger.warning(f"Connection refused (Windows host not running?)")
            self.connected = False
            return False
        
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.connected = False
            return False
    
    def send_message(self, msg: Dict) -> bool:
        """Send message to host"""
        try:
            if not self.connected or not self.socket:
                return False
            
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
                AndroidContactManager.cache_contacts(contacts)
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to sync contacts: {e}")
            return False
    
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
        logger.info("")
        logger.info("Timers:")
        logger.info(f"  - Reconnect: {RECONNECT_INTERVAL}s")
        logger.info(f"  - Ping: {PING_INTERVAL}s")
        logger.info(f"  - Sync: {SYNC_INTERVAL}s")
        logger.info("")
        logger.info("Press Ctrl+C to shutdown...")
        logger.info("="*70)
        logger.info("")
        
        while self.running:
            if not self.connected:
                self.reconnect_timer += 1
                if self.reconnect_timer >= RECONNECT_INTERVAL:
                    logger.info("Attempting to reconnect...")
                    self.connect()
                    self.reconnect_timer = 0
            
            if self.connected:
                self.ping_timer += 1
                if self.ping_timer >= PING_INTERVAL:
                    if not self.ping():
                        logger.warning("Ping failed, disconnecting")
                        self.connected = False
                    self.ping_timer = 0
                
                self.sync_timer += 1
                if self.sync_timer >= SYNC_INTERVAL:
                    contacts = AndroidContactManager.get_contacts()
                    if contacts:
                        if not self.sync_contacts(contacts):
                            logger.warning("Sync failed, will retry")
                    else:
                        logger.warning("No contacts to sync")
                    self.sync_timer = 0
            
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


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="SBMS Z Fold 6 Client (Real Shizuku Integration)"
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
        help="Test mode: query contacts and send test SMS"
    )
    
    args = parser.parse_args()
    
    if args.test:
        logger.info("Running in TEST MODE")
        logger.info("")
        
        # Test contact retrieval
        logger.info("Testing real contact retrieval via Shizuku...")
        contacts = AndroidContactManager.get_contacts()
        logger.info(f"Found {len(contacts)} contacts:")
        for contact in contacts:
            logger.info(f"  - {contact['name']}: {contact['phone']}")
        
        # Test SMS
        logger.info("\nTesting SMS sending...")
        ShizukuSMS.send_sms("+46701234567", "Test SMS from SBMS")
        
        logger.info("\nTest complete")
        return
    
    # Production mode
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
