#!/usr/bin/env python3
"""
SBMS Windows Host - Production Version

Central server for Samsung Bluetooth Message Service.
Manages device connections, contacts, and message routing.

Author: Alex Jonsson
Date: December 2025

Requirements:
- Python 3.8+
- sqlite3 (builtin)

Usage:
```bash
python sbms_windows_host.py
```
"""

import socket
import threading
import json
import sqlite3
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================

BLUETOOTH_PORT = 5555
TCP_PORT = 9999
BIND_HOST = "127.0.0.1"

DB_PATH = "sbms_host.db"
LOG_FILE = "sbms_host.log"

# ============================================================================
# Logging Setup
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# Database Setup
# ============================================================================

class Database:
    """SQLite database for SBMS host"""
    
    def __init__(self, path: str):
        self.path = path
        self.init_db()
    
    def init_db(self) -> None:
        """Initialize database schema"""
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        
        # Devices table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY,
            name TEXT,
            status TEXT,
            last_seen TIMESTAMP,
            last_ping TIMESTAMP,
            ip_address TEXT,
            port INTEGER
        )
        """)
        
        # Contacts table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            name TEXT,
            phone TEXT,
            added TIMESTAMP,
            last_contact TIMESTAMP,
            FOREIGN KEY(device_id) REFERENCES devices(id)
        )
        """)
        
        # Messages table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            device_id TEXT,
            to_number TEXT,
            text TEXT,
            status TEXT,
            timestamp TIMESTAMP,
            retry_count INTEGER DEFAULT 0,
            FOREIGN KEY(device_id) REFERENCES devices(id)
        )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized: {self.path}")
    
    def execute(self, query: str, params: Tuple = ()) -> List:
        """Execute query and return results"""
        try:
            conn = sqlite3.connect(self.path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall()
            conn.commit()
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Database error: {e}")
            return []
    
    def insert(self, query: str, params: Tuple = ()) -> bool:
        """Insert record"""
        try:
            conn = sqlite3.connect(self.path)
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Database insert error: {e}")
            return False


# ============================================================================
# Device Handler
# ============================================================================

class DeviceHandler(threading.Thread):
    """Handles individual device connections"""
    
    def __init__(self, client_socket: socket.socket, addr: Tuple, db: Database):
        super().__init__()
        self.client_socket = client_socket
        self.addr = addr
        self.db = db
        self.device_id = None
        self.device_name = None
        self.running = True
        self.daemon = True
    
    def run(self) -> None:
        """Handle device connection"""
        try:
            self.client_socket.settimeout(30)
            
            while self.running:
                try:
                    data = self.client_socket.recv(4096).decode('utf-8')
                    
                    if not data:
                        break
                    
                    # Parse JSON message
                    msg = json.loads(data)
                    self._handle_message(msg)
                
                except socket.timeout:
                    logger.debug(f"Device {self.device_id} timeout")
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON from {self.addr}: {e}")
                except Exception as e:
                    logger.error(f"Device handler error: {e}")
                    break
        
        finally:
            self.disconnect()
    
    def _handle_message(self, msg: Dict) -> None:
        """Handle incoming message from device"""
        msg_type = msg.get('type')
        
        if msg_type == 'identify':
            self.device_id = msg.get('device', f"device_{self.addr[1]}")
            self.device_name = msg.get('device')
            self._register_device()
            logger.info(f"Device identified: {self.device_name} ({self.device_id})")
        
        elif msg_type == 'ping':
            self._update_device_status()
        
        elif msg_type == 'sync_contacts':
            contacts = msg.get('contacts', [])
            self._sync_contacts(contacts)
            logger.info(f"Synced {len(contacts)} contacts from {self.device_name}")
        
        elif msg_type == 'send_message':
            msg_id = msg.get('id')
            to_number = msg.get('to')
            text = msg.get('text')
            self._queue_message(msg_id, to_number, text)
            logger.info(f"Queued message {msg_id} to {to_number}")
        
        elif msg_type == 'sms_status':
            msg_id = msg.get('id')
            status = msg.get('status')
            self._update_message_status(msg_id, status)
            logger.info(f"Message {msg_id} status: {status}")
    
    def _register_device(self) -> None:
        """Register device in database"""
        query = """
        INSERT OR REPLACE INTO devices (id, name, status, last_seen, ip_address, port)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        self.db.insert(query, (
            self.device_id,
            self.device_name,
            'online',
            datetime.now().isoformat(),
            self.addr[0],
            self.addr[1]
        ))
    
    def _update_device_status(self) -> None:
        """Update device last seen time"""
        query = "UPDATE devices SET last_ping = ? WHERE id = ?"
        self.db.insert(query, (datetime.now().isoformat(), self.device_id))
    
    def _sync_contacts(self, contacts: List[Dict]) -> None:
        """Sync contacts from device"""
        # Clear old contacts
        query = "DELETE FROM contacts WHERE device_id = ?"
        self.db.insert(query, (self.device_id,))
        
        # Insert new contacts
        for contact in contacts:
            query = """
            INSERT INTO contacts (device_id, name, phone, added, last_contact)
            VALUES (?, ?, ?, ?, ?)
            """
            self.db.insert(query, (
                self.device_id,
                contact.get('name'),
                contact.get('phone'),
                datetime.now().isoformat(),
                None
            ))
    
    def _queue_message(self, msg_id: str, to_number: str, text: str) -> None:
        """Queue message for sending"""
        query = """
        INSERT INTO messages (id, device_id, to_number, text, status, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        self.db.insert(query, (
            msg_id,
            self.device_id,
            to_number,
            text,
            'pending',
            datetime.now().isoformat()
        ))
    
    def _update_message_status(self, msg_id: str, status: str) -> None:
        """Update message delivery status"""
        query = "UPDATE messages SET status = ? WHERE id = ?"
        self.db.insert(query, (status, msg_id))
    
    def disconnect(self) -> None:
        """Disconnect device"""
        try:
            self.running = False
            if self.device_id:
                query = "UPDATE devices SET status = ? WHERE id = ?"
                self.db.insert(query, ('offline', self.device_id))
                logger.info(f"Device {self.device_name} disconnected")
            self.client_socket.close()
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")


# ============================================================================
# Host Server
# ============================================================================

class SBMSHost:
    """SBMS Windows Host server"""
    
    def __init__(self):
        self.db = Database(DB_PATH)
        self.devices = {}
        self.running = False
    
    def start(self) -> None:
        """Start SBMS host"""
        self.running = True
        
        logger.info("="*70)
        logger.info("Starting SBMS Windows Host")
        logger.info("="*70)
        
        # Start TCP server for Control Center
        tcp_thread = threading.Thread(target=self._start_tcp_server, daemon=True)
        tcp_thread.start()
        
        # Start Bluetooth/TCP server for devices
        device_thread = threading.Thread(target=self._start_device_server, daemon=True)
        device_thread.start()
        
        logger.info("="*70)
        logger.info("[OK] All services started successfully")
        logger.info("="*70)
        logger.info(f"Device port: {BLUETOOTH_PORT}")
        logger.info(f"Control Center port: {TCP_PORT}")
        logger.info("")
        logger.info("Press Ctrl+C to shut down...")
        logger.info("")
        
        try:
            while self.running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def _start_device_server(self) -> None:
        """Start server for device connections"""
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((BIND_HOST, BLUETOOTH_PORT))
            server.listen(5)
            
            logger.info(f"Device server listening on {BIND_HOST}:{BLUETOOTH_PORT}")
            
            while self.running:
                try:
                    client_socket, addr = server.accept()
                    logger.info(f"Device connection from {addr}")
                    
                    handler = DeviceHandler(client_socket, addr, self.db)
                    handler.start()
                    
                except Exception as e:
                    if self.running:
                        logger.error(f"Device accept error: {e}")
        
        except Exception as e:
            logger.error(f"Device server error: {e}")
        
        finally:
            try:
                server.close()
            except:
                pass
    
    def _start_tcp_server(self) -> None:
        """Start server for Control Center connections"""
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((BIND_HOST, TCP_PORT))
            server.listen(5)
            
            logger.info(f"Control Center server listening on {BIND_HOST}:{TCP_PORT}")
            
            while self.running:
                try:
                    client_socket, addr = server.accept()
                    logger.info(f"Control Center connection from {addr}")
                    
                    handler = threading.Thread(
                        target=self._handle_control_center,
                        args=(client_socket, addr),
                        daemon=True
                    )
                    handler.start()
                
                except Exception as e:
                    if self.running:
                        logger.error(f"Control Center accept error: {e}")
        
        except Exception as e:
            logger.error(f"Control Center server error: {e}")
        
        finally:
            try:
                server.close()
            except:
                pass
    
    def _handle_control_center(self, client_socket: socket.socket, addr: Tuple) -> None:
        """Handle Control Center requests"""
        try:
            client_socket.settimeout(10)
            
            while self.running:
                data = client_socket.recv(4096).decode('utf-8')
                
                if not data:
                    break
                
                msg = json.loads(data)
                response = self._handle_control_request(msg)
                
                client_socket.sendall(json.dumps(response).encode('utf-8'))
        
        except socket.timeout:
            pass
        except Exception as e:
            logger.error(f"Control Center handler error: {e}")
        
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def _handle_control_request(self, msg: Dict) -> Dict:
        """Handle Control Center API request"""
        msg_type = msg.get('type')
        
        if msg_type == 'get_status':
            devices = self.db.execute("SELECT COUNT(*) as count FROM devices WHERE status = 'online'")
            contacts = self.db.execute("SELECT COUNT(*) as count FROM contacts")
            messages = self.db.execute("SELECT COUNT(*) as count FROM messages")
            
            return {
                'status': 'ok',
                'devices_connected': devices[0]['count'] if devices else 0,
                'contacts_count': contacts[0]['count'] if contacts else 0,
                'messages_count': messages[0]['count'] if messages else 0
            }
        
        elif msg_type == 'get_contacts':
            contacts = self.db.execute("""
            SELECT phone, name, added, last_contact
            FROM contacts
            ORDER BY name
            """)
            
            data = {}
            for contact in contacts:
                data[contact['phone']] = {
                    'name': contact['name'],
                    'added': contact['added'],
                    'last_contact': contact['last_contact']
                }
            
            return {'status': 'ok', 'data': data}
        
        elif msg_type == 'get_messages':
            messages = self.db.execute("""
            SELECT id, to_number, text, status, timestamp, retry_count
            FROM messages
            ORDER BY timestamp DESC
            LIMIT 100
            """)
            
            data = {}
            for msg in messages:
                data[msg['id']] = {
                    'to_number': msg['to_number'],
                    'text': msg['text'],
                    'status': msg['status'],
                    'timestamp': msg['timestamp'],
                    'retry_count': msg['retry_count']
                }
            
            return {'status': 'ok', 'data': data}
        
        elif msg_type == 'send_message':
            msg_id = msg.get('id')
            to_number = msg.get('to')
            text = msg.get('text')
            
            query = """
            INSERT INTO messages (id, device_id, to_number, text, status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            self.db.insert(query, (
                msg_id,
                'local',
                to_number,
                text,
                'pending',
                datetime.now().isoformat()
            ))
            
            return {'status': 'queued'}
        
        return {'status': 'error', 'message': 'Unknown request'}
    
    def stop(self) -> None:
        """Stop SBMS host"""
        logger.info("")
        logger.info("="*70)
        logger.info("Shutting down SBMS Windows Host...")
        logger.info("="*70)
        
        self.running = False


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    host = SBMSHost()
    host.start()
