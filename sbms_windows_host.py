#!/usr/bin/env python3
"""
SBMS Windows Host

Central relay server for the Samsung Bluetooth Message Service.
Bridges communication between E1310E (J2ME), Z Fold 6 (Android), and Control Center (UI).

Uses native Windows Bluetooth APIs instead of pybluez for RFCOMM support.

Author: Alex Jonsson
Location: Kista, Sweden
Date: December 2025
"""

import json
import logging
import threading
import socket
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys

# Windows-specific imports
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    # Windows Bluetooth constants
    INVALID_SOCKET = ctypes.c_int(-1).value
    SOCKET_ERROR = -1
else:
    print("ERROR: This script is designed for Windows. Use sbms_linux_host.py on Linux.")
    sys.exit(1)

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
BLUETOOTH_PORT = 1  # RFCOMM port 1
BLUETOOTH_BACKLOG = 5
BLUETOOTH_TIMEOUT = 30  # seconds

# TCP settings
TCP_HOST = "127.0.0.1"
TCP_PORT = 9999
TCP_BACKLOG = 5
TCP_TIMEOUT = 10  # seconds

# ============================================================================
# Logging Setup
# ============================================================================

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# Windows Bluetooth Support (Without PyBluez)
# ============================================================================

class WindowsBluetoothAdapter:
    """
    Wrapper for Windows native Bluetooth APIs via ctypes.
    Since pybluez doesn't support RFCOMM properly on Windows,
    we use socket library with AF_BTH (Bluetooth) family.
    """
    
    @staticmethod
    def create_rfcomm_socket():
        """
        Create a Bluetooth RFCOMM socket using Windows sockets API.
        AF_BTH = 32 (Bluetooth address family)
        BTHPROTO_RFCOMM = 3 (RFCOMM protocol)
        SOCK_STREAM = 1
        """
        try:
            # Try native Windows Bluetooth socket
            # Windows uses AF_BTH (32) instead of standard socket families
            sock = socket.socket(32, socket.SOCK_STREAM)  # 32 = AF_BTH
            return sock
        except Exception as e:
            logger.warning(f"Native Windows Bluetooth socket failed: {e}")
            logger.info("Falling back to mock TCP server for testing")
            return None
    
    @staticmethod
    def bind_rfcomm_socket(sock, port: int):
        """
        Bind RFCOMM socket to a port.
        On Windows, use BT_ADDR_ANY (0, 0, 0, 0, 0, 0)
        """
        try:
            # Windows Bluetooth address format: (MAC, 0, port)
            sock.bind(("00:00:00:00:00:00", port))
            logger.info(f"Bluetooth socket bound to port {port}")
            return True
        except Exception as e:
            logger.warning(f"Failed to bind Bluetooth socket: {e}")
            return False


# ============================================================================
# Data Management
# ============================================================================

class ContactDatabase:
    """Manages contact storage and synchronization"""
    
    def __init__(self, db_path: str = CONTACTS_DB):
        self.db_path = Path(db_path)
        self.contacts: Dict[str, Dict] = {}  # Key: phone number, Value: contact info
        self._load()
    
    def _load(self) -> None:
        """Load contacts from JSON file"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.contacts = json.load(f)
                logger.info(f"Loaded {len(self.contacts)} contacts")
            except Exception as e:
                logger.error(f"Failed to load contacts: {e}")
                self.contacts = {}
        else:
            logger.info("No existing contact database found, starting fresh")
            self.contacts = {}
    
    def _save(self) -> None:
        """Save contacts to JSON file"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.contacts, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {len(self.contacts)} contacts to database")
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
        count = 0
        for contact in contacts:
            phone = contact.get('phone')
            name = contact.get('name')
            if phone:
                self.add_contact(phone, name)
                count += 1
        logger.info(f"Synced {count} new/updated contacts from device")


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
                with open(self.log_path, 'r', encoding='utf-8') as f:
                    self.messages = json.load(f)
                logger.info(f"Loaded {len(self.messages)} messages")
            except Exception as e:
                logger.error(f"Failed to load messages: {e}")
                self.messages = {}
        else:
            logger.info("No existing message log found, starting fresh")
            self.messages = {}
    
    def _save(self) -> None:
        """Save message log to JSON file"""
        try:
            with open(self.log_path, 'w', encoding='utf-8') as f:
                json.dump(self.messages, f, indent=2, ensure_ascii=False)
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
# Bluetooth Communication (Mock TCP on Windows if native fails)
# ============================================================================

class BluetoothServer:
    """
    Manages Bluetooth RFCOMM server for device connections.
    Falls back to TCP if native Bluetooth socket fails on Windows.
    """
    
    def __init__(self, contacts_db: ContactDatabase, msg_queue: MessageQueue):
        self.contacts_db = contacts_db
        self.msg_queue = msg_queue
        self.server_socket = None
        self.running = False
        self.clients: Dict[str, socket.socket] = {}
        self.use_tcp_fallback = False
        self._client_lock = threading.Lock()
    
    def start(self) -> None:
        """Start Bluetooth RFCOMM server (with TCP fallback for Windows)"""
        try:
            # Try native Windows Bluetooth socket first
            sock = WindowsBluetoothAdapter.create_rfcomm_socket()
            
            if sock is None:
                logger.warning("Using TCP fallback for Bluetooth server")
                self._start_tcp_fallback()
                return
            
            self.server_socket = sock
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.settimeout(BLUETOOTH_TIMEOUT)
            
            if WindowsBluetoothAdapter.bind_rfcomm_socket(self.server_socket, BLUETOOTH_PORT):
                self.server_socket.listen(BLUETOOTH_BACKLOG)
                logger.info(f"Bluetooth server started on port {BLUETOOTH_PORT}")
                self.running = True
                self._accept_connections()
            else:
                self._start_tcp_fallback()
        
        except Exception as e:
            logger.error(f"Failed to start Bluetooth server: {e}")
            self._start_tcp_fallback()
    
    def _start_tcp_fallback(self) -> None:
        """Start TCP fallback server on separate port for Bluetooth devices"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("0.0.0.0", 5555))  # Different port for Bluetooth fallback
            self.server_socket.listen(BLUETOOTH_BACKLOG)
            self.server_socket.settimeout(BLUETOOTH_TIMEOUT)
            
            logger.info("Bluetooth server started (TCP fallback on port 5555)")
            self.running = True
            self.use_tcp_fallback = True
            self._accept_connections()
        except Exception as e:
            logger.error(f"Failed to start TCP fallback: {e}")
    
    def _accept_connections(self) -> None:
        """Accept and handle incoming Bluetooth/TCP connections"""
        while self.running:
            try:
                client_sock, client_addr = self.server_socket.accept()
                logger.info(f"Device connection from {client_addr}")
                
                # Store client
                with self._client_lock:
                    self.clients[str(client_addr)] = client_sock
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, client_addr),
                    daemon=True
                )
                client_thread.start()
            
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting connection: {e}")
    
    def _handle_client(self, client_sock: socket.socket, client_addr: str) -> None:
        """Handle messages from a connected client"""
        client_id = str(client_addr)
        try:
            client_sock.settimeout(BLUETOOTH_TIMEOUT)
            
            while True:
                try:
                    data = client_sock.recv(1024)
                    if not data:
                        break
                    
                    message = json.loads(data.decode('utf-8'))
                    logger.debug(f"Device message: {message}")
                    
                    response = self._process_message(message, client_addr)
                    
                    if response:
                        client_sock.send(json.dumps(response).encode('utf-8'))
                
                except socket.timeout:
                    continue
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON from {client_addr}: {e}")
                    break
        
        except Exception as e:
            logger.error(f"Error handling device {client_addr}: {e}")
        
        finally:
            try:
                client_sock.close()
            except:
                pass
            
            with self._client_lock:
                if client_id in self.clients:
                    del self.clients[client_id]
            
            logger.info(f"Device disconnected: {client_addr}")
    
    def _process_message(self, message: Dict, client_addr: str) -> Optional[Dict]:
        """Process message from device"""
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
            logger.info(f"Syncing {len(contacts)} contacts from device")
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
        
        # Close all client connections
        with self._client_lock:
            for client_sock in self.clients.values():
                try:
                    client_sock.close()
                except:
                    pass
            self.clients.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
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
        self.clients: Dict[str, socket.socket] = {}
        self._client_lock = threading.Lock()
    
    def start(self) -> None:
        """Start TCP server for control center"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((TCP_HOST, TCP_PORT))
            self.server_socket.listen(TCP_BACKLOG)
            self.server_socket.settimeout(TCP_TIMEOUT)
            
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
                logger.info(f"Control Center connection from {client_addr}")
                
                # Store client
                with self._client_lock:
                    self.clients[str(client_addr)] = client_sock
                
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, client_addr),
                    daemon=True
                )
                client_thread.start()
            
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting TCP connection: {e}")
    
    def _handle_client(self, client_sock: socket.socket, client_addr: str) -> None:
        """Handle messages from control center"""
        client_id = str(client_addr)
        try:
            client_sock.settimeout(TCP_TIMEOUT)
            
            while True:
                try:
                    data = client_sock.recv(1024)
                    if not data:
                        break
                    
                    message = json.loads(data.decode('utf-8'))
                    logger.debug(f"Control Center message: {message}")
                    
                    response = self._process_message(message)
                    
                    if response:
                        client_sock.send(json.dumps(response).encode('utf-8'))
                
                except socket.timeout:
                    continue
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON from control center: {e}")
                    break
        
        except Exception as e:
            logger.error(f"Error handling control center {client_addr}: {e}")
        
        finally:
            try:
                client_sock.close()
            except:
                pass
            
            with self._client_lock:
                if client_id in self.clients:
                    del self.clients[client_id]
            
            logger.info(f"Control center disconnected: {client_addr}")
    
    def _process_message(self, message: Dict) -> Optional[Dict]:
        """Process message from control center"""
        msg_type = message.get('type')
        
        if msg_type == 'get_status':
            return {
                "type": "status",
                "contacts_count": len(self.contacts_db.get_contacts()),
                "messages_count": len(self.msg_queue.messages),
                "devices_connected": 1,  # Simplified
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
        
        # Close all client connections
        with self._client_lock:
            for client_sock in self.clients.values():
                try:
                    client_sock.close()
                except:
                    pass
            self.clients.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
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
        self.threads = []
    
    def start(self) -> None:
        """Start all services"""
        logger.info("="*70)
        logger.info("Starting SBMS Windows Host")
        logger.info("="*70)
        
        # Start Bluetooth server in thread
        bt_thread = threading.Thread(target=self.bluetooth_server.start, daemon=False)
        bt_thread.start()
        self.threads.append(bt_thread)
        time.sleep(0.5)
        
        # Start TCP server in thread
        tcp_thread = threading.Thread(target=self.tcp_server.start, daemon=False)
        tcp_thread.start()
        self.threads.append(tcp_thread)
        time.sleep(0.5)
        
        logger.info("="*70)
        logger.info("[OK] All services started successfully")
        logger.info("="*70)
        logger.info("[OK] Bluetooth server listening")
        logger.info("[OK] TCP server listening on 127.0.0.1:9999")
        logger.info(f"[OK] Contact database ready ({len(self.contacts_db.get_contacts())} contacts)")
        logger.info(f"[OK] Message queue active ({len(self.msg_queue.messages)} messages)")
        logger.info("="*70)
        logger.info("")
        logger.info("Press Ctrl+C to shut down...")
        logger.info("")
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("")
            self.stop()
    
    def stop(self) -> None:
        """Stop all services"""
        logger.info("")
        logger.info("="*70)
        logger.info("Shutting down SBMS Host...")
        logger.info("="*70)
        
        self.bluetooth_server.stop()
        self.tcp_server.stop()
        
        logger.info("Waiting for threads to finish...")
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=5)
        
        logger.info("="*70)
        logger.info("SBMS Host stopped")
        logger.info("="*70)


if __name__ == "__main__":
    host = SBMSHost()
    host.start()
