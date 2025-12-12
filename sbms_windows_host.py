#!/usr/bin/env python3
"""
SBMS Windows Host

Central relay server for the Samsung Bluetooth Message Service.
Bridges communication between E1310E (J2ME), Z Fold 6 (Android), and Control Center (UI).

Author: Alex Jonsson
Location: Kista, Sweden
Date: December 2025
"""

import json
import logging
import threading
import socket
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import bluetooth
except ImportError:
    print("ERROR: pybluez not installed. Install with: pip install pybluez")
    exit(1)

# ============================================================================
# Configuration
# ============================================================================

LOG_FILE = "sbms_host.log"
CONTACTS_DB = "contacts.json"
MESSAGE_LOG = "messages.json"

# Device MAC addresses (configure these for your devices)
E1310E_MAC = "E1:31:0E:XX:XX:XX"  # Samsung E1310E
ZFOLD6_MAC = "XX:XX:XX:XX:XX:XX"  # Samsung Z Fold 6

# Bluetooth settings
BLUETOOTH_PORT = 1
BLUETOOTH_BACKLOG = 1

# TCP settings
TCP_HOST = "127.0.0.1"
TCP_PORT = 9999
TCP_BACKLOG = 5

# ============================================================================
# Logging Setup
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# Data Management
# ============================================================================

class ContactDatabase:
    """Manages contact storage and synchronization"""
    
    def __init__(self, db_path: str = CONTACTS_DB):
        self.db_path = Path(db_path)
        self.contacts: Dict[str, Dict] = {}
        self._load()
    
    def _load(self) -> None:
        """Load contacts from JSON file"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r') as f:
                    self.contacts = json.load(f)
                logger.info(f"Loaded {len(self.contacts)} contacts")
            except Exception as e:
                logger.error(f"Failed to load contacts: {e}")
                self.contacts = {}
        else:
            logger.info("No existing contact database found")
    
    def _save(self) -> None:
        """Save contacts to JSON file"""
        try:
            with open(self.db_path, 'w') as f:
                json.dump(self.contacts, f, indent=2)
            logger.debug(f"Saved {len(self.contacts)} contacts")
        except Exception as e:
            logger.error(f"Failed to save contacts: {e}")
    
    def add_contact(self, phone: str, name: str) -> None:
        """Add or update a contact"""
        self.contacts[phone] = {
            "name": name,
            "phone": phone,
            "added": datetime.now().isoformat(),
            "last_contact": None
        }
        self._save()
        logger.info(f"Added/updated contact: {name} ({phone})")
    
    def get_contacts(self) -> Dict:
        """Get all contacts"""
        return self.contacts
    
    def sync_from_device(self, contacts: List[Dict]) -> None:
        """Sync contacts from Z Fold 6 or other device"""
        for contact in contacts:
            self.add_contact(contact.get('phone'), contact.get('name'))
        logger.info(f"Synced {len(contacts)} contacts from device")


class MessageQueue:
    """Manages message routing and delivery tracking"""
    
    def __init__(self, log_path: str = MESSAGE_LOG):
        self.log_path = Path(log_path)
        self.messages: Dict[str, Dict] = {}
        self._load()
    
    def _load(self) -> None:
        """Load message log from JSON file"""
        if self.log_path.exists():
            try:
                with open(self.log_path, 'r') as f:
                    self.messages = json.load(f)
                logger.info(f"Loaded {len(self.messages)} messages")
            except Exception as e:
                logger.error(f"Failed to load messages: {e}")
                self.messages = {}
    
    def _save(self) -> None:
        """Save message log to JSON file"""
        try:
            with open(self.log_path, 'w') as f:
                json.dump(self.messages, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save messages: {e}")
    
    def add_message(self, msg_id: str, to_number: str, text: str, from_device: str) -> None:
        """Add message to queue"""
        self.messages[msg_id] = {
            "id": msg_id,
            "from_device": from_device,
            "to_number": to_number,
            "text": text,
            "status": "pending",
            "timestamp": datetime.now().isoformat(),
            "retry_count": 0
        }
        self._save()
        logger.info(f"Added message {msg_id} to {to_number}")
    
    def update_status(self, msg_id: str, status: str) -> None:
        """Update message delivery status"""
        if msg_id in self.messages:
            self.messages[msg_id]["status"] = status
            self._save()
            logger.info(f"Message {msg_id} status: {status}")


# ============================================================================
# Bluetooth Communication
# ============================================================================

class BluetoothServer:
    """Manages Bluetooth RFCOMM server for device connections"""
    
    def __init__(self, contacts_db: ContactDatabase, msg_queue: MessageQueue):
        self.contacts_db = contacts_db
        self.msg_queue = msg_queue
        self.server_socket = None
        self.running = False
        self.clients: Dict[str, socket.socket] = {}
    
    def start(self) -> None:
        """Start Bluetooth RFCOMM server"""
        try:
            self.server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.server_socket.bind(("", BLUETOOTH_PORT))
            self.server_socket.listen(BLUETOOTH_BACKLOG)
            
            local_addr = bluetooth.read_local_bdaddr()[0]
            logger.info(f"Bluetooth server started on {local_addr}:{BLUETOOTH_PORT}")
            
            self.running = True
            self._accept_connections()
        except Exception as e:
            logger.error(f"Failed to start Bluetooth server: {e}")
    
    def _accept_connections(self) -> None:
        """Accept and handle incoming Bluetooth connections"""
        while self.running:
            try:
                client_sock, client_addr = self.server_socket.accept()
                logger.info(f"Bluetooth connection from {client_addr}")
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, client_addr),
                    daemon=True
                )
                client_thread.start()
            except Exception as e:
                logger.error(f"Error accepting connection: {e}")
    
    def _handle_client(self, client_sock: socket.socket, client_addr: str) -> None:
        """Handle messages from a connected client"""
        try:
            while True:
                data = client_sock.recv(1024).decode('utf-8')
                if not data:
                    break
                
                message = json.loads(data)
                logger.debug(f"Received: {message}")
                
                response = self._process_message(message, client_addr)
                
                if response:
                    client_sock.send(json.dumps(response).encode('utf-8'))
        except Exception as e:
            logger.error(f"Error handling client {client_addr}: {e}")
        finally:
            client_sock.close()
            logger.info(f"Disconnected: {client_addr}")
    
    def _process_message(self, message: Dict, client_addr: str) -> Optional[Dict]:
        """Process message from client"""
        msg_type = message.get('type')
        
        if msg_type == 'identify':
            device = message.get('device')
            logger.info(f"Device identified: {device}")
            return {"type": "ack", "status": "identified"}
        
        elif msg_type == 'get_contacts':
            contacts = self.contacts_db.get_contacts()
            return {"type": "contacts", "data": contacts}
        
        elif msg_type == 'sync_contacts':
            contacts = message.get('contacts', [])
            self.contacts_db.sync_from_device(contacts)
            return {"type": "ack", "status": "synced"}
        
        elif msg_type == 'send_message':
            msg_id = message.get('id')
            to_num = message.get('to')
            text = message.get('text')
            self.msg_queue.add_message(msg_id, to_num, text, str(client_addr))
            return {"type": "ack", "status": "queued", "id": msg_id}
        
        elif msg_type == 'sms_status':
            msg_id = message.get('id')
            status = message.get('status')
            self.msg_queue.update_status(msg_id, status)
            return {"type": "ack", "status": "received"}
        
        elif msg_type == 'ping':
            return {"type": "pong"}
        
        else:
            logger.warning(f"Unknown message type: {msg_type}")
            return {"type": "error", "message": "Unknown message type"}
    
    def stop(self) -> None:
        """Stop Bluetooth server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        logger.info("Bluetooth server stopped")


# ============================================================================
# TCP Control Center Connection
# ============================================================================

class TCPServer:
    """Manages TCP server for control center UI connections"""
    
    def __init__(self, contacts_db: ContactDatabase, msg_queue: MessageQueue):
        self.contacts_db = contacts_db
        self.msg_queue = msg_queue
        self.server_socket = None
        self.running = False
    
    def start(self) -> None:
        """Start TCP server for control center"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((TCP_HOST, TCP_PORT))
            self.server_socket.listen(TCP_BACKLOG)
            
            logger.info(f"TCP server started on {TCP_HOST}:{TCP_PORT}")
            
            self.running = True
            self._accept_connections()
        except Exception as e:
            logger.error(f"Failed to start TCP server: {e}")
    
    def _accept_connections(self) -> None:
        """Accept and handle incoming TCP connections"""
        while self.running:
            try:
                client_sock, client_addr = self.server_socket.accept()
                logger.info(f"TCP connection from {client_addr}")
                
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, client_addr),
                    daemon=True
                )
                client_thread.start()
            except Exception as e:
                logger.error(f"Error accepting TCP connection: {e}")
    
    def _handle_client(self, client_sock: socket.socket, client_addr: str) -> None:
        """Handle messages from control center"""
        try:
            while True:
                data = client_sock.recv(1024).decode('utf-8')
                if not data:
                    break
                
                message = json.loads(data)
                logger.debug(f"Control Center: {message}")
                
                response = self._process_message(message)
                
                if response:
                    client_sock.send(json.dumps(response).encode('utf-8'))
        except Exception as e:
            logger.error(f"Error handling control center {client_addr}: {e}")
        finally:
            client_sock.close()
            logger.info(f"Control center disconnected: {client_addr}")
    
    def _process_message(self, message: Dict) -> Optional[Dict]:
        """Process message from control center"""
        msg_type = message.get('type')
        
        if msg_type == 'get_status':
            return {
                "type": "status",
                "contacts_count": len(self.contacts_db.get_contacts()),
                "messages_count": len(self.msg_queue.messages),
                "timestamp": datetime.now().isoformat()
            }
        
        elif msg_type == 'get_contacts':
            return {
                "type": "contacts",
                "data": self.contacts_db.get_contacts()
            }
        
        elif msg_type == 'get_messages':
            return {
                "type": "messages",
                "data": self.msg_queue.messages
            }
        
        else:
            return {"type": "error", "message": "Unknown request"}
    
    def stop(self) -> None:
        """Stop TCP server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        logger.info("TCP server stopped")


# ============================================================================
# Main Application
# ============================================================================

class SBMSHost:
    """Main SBMS Windows Host application"""
    
    def __init__(self):
        self.contacts_db = ContactDatabase()
        self.msg_queue = MessageQueue()
        self.bluetooth_server = BluetoothServer(self.contacts_db, self.msg_queue)
        self.tcp_server = TCPServer(self.contacts_db, self.msg_queue)
    
    def start(self) -> None:
        """Start all services"""
        logger.info("="*60)
        logger.info("Starting SBMS Windows Host")
        logger.info("="*60)
        
        # Start Bluetooth server in thread
        bt_thread = threading.Thread(target=self.bluetooth_server.start, daemon=True)
        bt_thread.start()
        
        # Start TCP server in thread
        tcp_thread = threading.Thread(target=self.tcp_server.start, daemon=True)
        tcp_thread.start()
        
        logger.info("All services started")
        logger.info("\u2713 Bluetooth server listening")
        logger.info("\u2713 TCP server listening")
        logger.info("\u2713 Contact database ready")
        logger.info("\u2713 Message queue active")
        
        # Keep running
        try:
            while True:
                input()
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self) -> None:
        """Stop all services"""
        logger.info("Shutting down SBMS Host...")
        self.bluetooth_server.stop()
        self.tcp_server.stop()
        logger.info("SBMS Host stopped")


if __name__ == "__main__":
    host = SBMSHost()
    host.start()
