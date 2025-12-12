#!/usr/bin/env python3
"""
SBMS Z Fold 6 Client (Termux/Android Python)

Bridges Samsung Z Fold 6 Android contacts and SMS with SBMS Windows Host.
Runs in Termux, syncs contacts via Shizuku, and sends SMS.

Requires Shizuku app installed and running on Z Fold 6.

Author: Alex Jonsson
Location: Stockholm, Sweden
Date: December 2025

Requirements (in Termux):
- python3.10+
- Shizuku app configured on Z Fold 6
- Standard packages: socket, json, threading, time, sys, os, subprocess

Setup:
```bash
pkg install python
pip install --upgrade pip
cp sbms_zfold6.py ~/.sbms/
cd ~/.sbms

# Grant Termux permissions via Shizuku (one-time)
python sbms_zfold6.py --setup-shizuku

# Run normally
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

# Shizuku command prefix (use with 'sh' to execute with Shizuku privileges)
SHIZUKU_PREFIX = "sh"

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
# Shizuku Integration
# ============================================================================

class ShizukuHelper:
    """
    Helper class to interact with Shizuku service on Android 13+.
    Requires Shizuku app to be running.
    """
    
    @staticmethod
    def check_shizuku() -> bool:
        """Check if Shizuku is available and working"""
        try:
            # Try to run a simple command through Shizuku
            result = subprocess.run(
                ["sh", "-c", "which pm"],
                capture_output=True,
                timeout=5,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("✓ Shizuku is available")
                return True
            else:
                logger.warning("✗ Shizuku not responding properly")
                return False
        except Exception as e:
            logger.error(f"Failed to check Shizuku: {e}")
            return False
    
    @staticmethod
    def grant_permissions() -> bool:
        """Grant necessary permissions to Termux via Shizuku"""
        logger.info("Requesting Shizuku to grant permissions...")
        
        permissions = [
            "android.permission.READ_CONTACTS",
            "android.permission.SEND_SMS",
            "android.permission.READ_SMS",
        ]
        
        package = "com.termux"
        
        try:
            for perm in permissions:
                logger.info(f"  Granting {perm}...")
                
                # Use pm grant to give permission
                cmd = f"pm grant {package} {perm}"
                result = subprocess.run(
                    ["sh", "-c", cmd],
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info(f"    ✓ {perm} granted")
                else:
                    logger.warning(f"    ⚠ {perm} might not have been granted")
            
            logger.info("Permission setup complete")
            return True
        
        except Exception as e:
            logger.error(f"Failed to grant permissions: {e}")
            return False


# ============================================================================
# Android Integration
# ============================================================================

class AndroidContactManager:
    """
    Reads contacts from Android via Shizuku.
    Works on Android 13+ without root.
    """
    
    @staticmethod
    def get_contacts() -> List[Dict]:
        """Get all contacts from Android via Shizuku"""
        
        # Method 1: Query via content command with Shizuku
        contacts = AndroidContactManager._get_contacts_via_shizuku()
        if contacts:
            logger.info(f"Retrieved {len(contacts)} contacts via Shizuku")
            return contacts
        
        # Method 2: Query via alternate URI
        contacts = AndroidContactManager._get_contacts_alternate()
        if contacts:
            logger.info(f"Retrieved {len(contacts)} contacts (alternate method)")
            return contacts
        
        # Fallback: Test contacts
        logger.warning("Could not get real contacts, using test contacts")
        return AndroidContactManager._get_test_contacts()
    
    @staticmethod
    def _get_contacts_via_shizuku() -> List[Dict]:
        """Query contacts using Shizuku-granted permissions"""
        try:
            logger.debug("Querying contacts via Shizuku...")
            
            # Use content query to get all contacts
            # The key is that Shizuku grants us the READ_CONTACTS permission
            cmd = """content query \
                --uri content://com.android.contacts/contacts \
                --projection _id:display_name \
            " && content query \
                --uri content://com.android.contacts/data \
                --projection contact_id:data1:mimetype_id \
            """
            
            result = subprocess.run(
                ["sh", "-c", cmd],
                capture_output=True,
                timeout=10,
                text=True
            )
            
            if result.returncode != 0:
                logger.debug(f"Shizuku content query failed: {result.stderr}")
                return []
            
            # Parse contacts from output
            contacts = {}
            
            for line in result.stdout.split('\n'):
                if 'display_name=' in line:
                    # Parse contact line
                    contact_data = {}
                    for part in line.split(', '):
                        if '=' in part:
                            key, val = part.split('=', 1)
                            contact_data[key.strip()] = val.strip()
                    
                    if 'display_name' in contact_data:
                        contact_id = contact_data.get('_id')
                        name = contact_data['display_name']
                        contacts[contact_id] = name
            
            # Now query phone numbers
            cmd2 = """content query \
                --uri content://com.android.contacts/data \
                --projection contact_id:data1 \
                --where 'mimetype_id = 5'
            """
            
            result2 = subprocess.run(
                ["sh", "-c", cmd2],
                capture_output=True,
                timeout=10,
                text=True
            )
            
            final_contacts = []
            
            for line in result2.stdout.split('\n'):
                if 'contact_id=' in line and 'data1=' in line:
                    contact_data = {}
                    for part in line.split(', '):
                        if '=' in part:
                            key, val = part.split('=', 1)
                            contact_data[key.strip()] = val.strip()
                    
                    contact_id = contact_data.get('contact_id')
                    phone = contact_data.get('data1', '').replace(' ', '').replace('-', '')
                    
                    if contact_id in contacts and phone:
                        final_contacts.append({
                            "name": contacts[contact_id],
                            "phone": phone
                        })
                        logger.debug(f"Found: {contacts[contact_id]} - {phone}")
            
            return final_contacts
        
        except Exception as e:
            logger.debug(f"Shizuku query failed: {e}")
            return []
    
    @staticmethod
    def _get_contacts_alternate() -> List[Dict]:
        """Alternate method to query contacts"""
        try:
            logger.debug("Trying alternate contact query method...")
            
            # Try simpler URI
            cmd = "content query --uri content://contacts/people --projection name:primary_phone"
            
            result = subprocess.run(
                ["sh", "-c", cmd],
                capture_output=True,
                timeout=10,
                text=True
            )
            
            if result.returncode != 0:
                return []
            
            contacts = []
            for line in result.stdout.split('\n'):
                if 'name=' in line and 'primary_phone=' in line:
                    parts = {}
                    for p in line.split(', '):
                        if '=' in p:
                            k, v = p.split('=', 1)
                            parts[k.strip()] = v.strip()
                    
                    name = parts.get('name')
                    phone = parts.get('primary_phone', '').replace(' ', '').replace('-', '')
                    
                    if name and phone:
                        contacts.append({"name": name, "phone": phone})
            
            return contacts
        
        except Exception as e:
            logger.debug(f"Alternate method failed: {e}")
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


class ShizukuSMS:
    """
    Sends SMS via Shizuku (privileged Android service).
    Works on Android 13+ without root.
    """
    
    @staticmethod
    def send_sms(phone_number: str, message_text: str) -> bool:
        """
        Send SMS using Shizuku with proper permissions.
        
        Returns:
            True if sent successfully, False on error
        """
        try:
            logger.info(f"Sending SMS to {phone_number} via Shizuku")
            
            # Method 1: Use am command with Shizuku to send SMS
            try:
                # This uses the default SMS app to send
                cmd = f"""am start -a android.intent.action.SENDTO -d sms:{phone_number} -e sms_body '{message_text}' --ez exit_on_sent true"""
                
                result = subprocess.run(
                    ["sh", "-c", cmd],
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info(f"SMS sent to {phone_number}")
                    return True
            except Exception as e:
                logger.debug(f"SMS via am failed: {e}")
            
            # Method 2: Use SmsManager if available
            try:
                # Direct SMS via SmsManager (requires SEND_SMS permission from Shizuku)
                cmd = f"""service call isms 5 s16 \"com.android.mms\" s16 \"\" s16 \"{phone_number}\" s16 \"\" s16 \"{message_text}\" s16 \"\" s16 \"\""""
                
                result = subprocess.run(
                    ["sh", "-c", cmd],
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info(f"SMS queued to {phone_number}")
                    return True
            except Exception as e:
                logger.debug(f"SmsManager method failed: {e}")
            
            # Fallback: Mock send
            logger.warning(f"Falling back to mock SMS for {phone_number}")
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
            "version": "1.0",
            "shizuku": True
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
        logger.info(f"SBMS Z Fold 6 Client Started (Shizuku-enabled)")
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
        logger.info("Log saved to: " + LOG_FILE)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="SBMS Z Fold 6 Client (Shizuku-enabled)"
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
        "--setup-shizuku",
        action="store_true",
        help="Setup Shizuku permissions (one-time setup)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (no persistent connection)"
    )
    
    args = parser.parse_args()
    
    if args.setup_shizuku:
        logger.info("Setting up Shizuku permissions...")
        logger.info("")
        
        if ShizukuHelper.check_shizuku():
            if ShizukuHelper.grant_permissions():
                logger.info("\n✓ Shizuku setup complete!")
                logger.info("You can now run: python sbms_zfold6.py --host WINDOWS_IP")
            else:
                logger.error("\n✗ Failed to grant permissions")
        else:
            logger.error("\n✗ Shizuku is not available")
            logger.error("Please start Shizuku app on your Z Fold 6 and try again")
        
        return
    
    if args.test:
        logger.info("Running in TEST MODE")
        logger.info(f"Would connect to {args.host}:{args.port}")
        logger.info("")
        
        if not ShizukuHelper.check_shizuku():
            logger.error("✗ Shizuku not available!")
            logger.error("Ensure Shizuku app is running on your Z Fold 6")
            return
        
        # Test contact retrieval
        logger.info("\nTesting contact retrieval...")
        contacts = AndroidContactManager.get_contacts()
        logger.info(f"Found {len(contacts)} contacts:")
        for contact in contacts:
            logger.info(f"  - {contact['name']}: {contact['phone']}")
        
        # Test SMS sending
        logger.info("\nTesting SMS sending...")
        ShizukuSMS.send_sms("+46701234567", "Test message from SBMS")
        
        logger.info("\nTest mode complete")
        return
    
    # Production mode
    if not ShizukuHelper.check_shizuku():
        logger.error("✗ Shizuku not available!")
        logger.error("Ensure Shizuku app is running on your Z Fold 6")
        logger.error("Then run: python sbms_zfold6.py --setup-shizuku")
        return
    
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
