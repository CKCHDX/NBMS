#!/usr/bin/env python3
"""
SBMS Z Fold 6 Client (Termux/Android Python)

Bridges Samsung Z Fold 6 Android contacts and SMS with SBMS Windows Host.
Runs in Termux, syncs contacts, and sends SMS.

Author: Alex Jonsson
Location: Stockholm, Sweden
Date: December 2025

Requirements (in Termux):
- python3.10+
- socket (builtin)
- json (builtin)
- threading (builtin)

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
    Manages Android contacts.
    Currently uses test contacts, will integrate real contacts via Rish/Shizuku later.
    """
    
    @staticmethod
    def get_contacts() -> List[Dict]:
        """Get contacts (currently test contacts)"""
        # TODO: Integrate with Rish/Shizuku for real contacts
        return AndroidContactManager._get_test_contacts()
    
    @staticmethod
    def _get_test_contacts() -> List[Dict]:
        """Return test contacts for development"""
        logger.debug("Using test contacts")
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


class SMS:
    """
    Sends SMS (currently mock, will integrate with Rish/Shizuku later).
    """
    
    @staticmethod
    def send_sms(phone_number: str, message_text: str) -> bool:
        """
        Send SMS.
        
        Returns:
            True if sent successfully, False on error
        """
        try:
            logger.info(f"Sending SMS to {phone_number}")
            logger.info(f"  Text: {message_text}")
            
            # TODO: Integrate with Rish/Shizuku for real SMS
            # For now, just log it
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
        description="SBMS Z Fold 6 Client"
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
        logger.info("")
        
        # Test contact retrieval
        logger.info("Testing contact retrieval...")
        contacts = AndroidContactManager.get_contacts()
        logger.info(f"Found {len(contacts)} contacts:")
        for contact in contacts:
            logger.info(f"  - {contact['name']}: {contact['phone']}")
        
        # Test SMS sending
        logger.info("\nTesting SMS sending...")
        SMS.send_sms("+46701234567", "Test message from SBMS")
        
        logger.info("\nTest mode complete")
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
