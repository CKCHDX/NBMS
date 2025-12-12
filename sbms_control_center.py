#!/usr/bin/env python3
"""
SBMS Control Center UI

PyQt6 desktop application for managing SBMS system.
Provides real-time monitoring and control of Windows host, connected devices,
contacts, and message delivery.

Author: Alex Jonsson
Location: Kista, Sweden
Date: December 2025

Requirements:
- Python 3.8+
- PyQt6 (pip install PyQt6)
"""

import json
import logging
import socket
import threading
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel,
        QTabWidget, QStatusBar, QMessageBox, QTextEdit, QComboBox,
        QSpinBox, QDialog, QFormLayout
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
    from PyQt6.QtGui import QColor, QFont, QIcon
except ImportError:
    print("ERROR: PyQt6 not installed. Install with: pip install PyQt6")
    sys.exit(1)

# ============================================================================
# Configuration
# ============================================================================

HOST_IP = "127.0.0.1"
HOST_PORT = 9999
LOG_FILE = "control_center.log"

UPDATE_INTERVAL = 1000  # milliseconds

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
# Host Communication
# ============================================================================

class HostConnection:
    """Manages connection to SBMS Windows Host"""
    
    def __init__(self):
        self.socket = None
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to Windows host"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((HOST_IP, HOST_PORT))
            self.connected = True
            logger.info(f"Connected to host {HOST_IP}:{HOST_PORT}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.connected = False
            return False
    
    def send_request(self, request: Dict) -> Optional[Dict]:
        """Send request to host and receive response"""
        try:
            if not self.connected:
                return None
            
            data = json.dumps(request).encode('utf-8')
            self.socket.send(data)
            
            response_data = self.socket.recv(4096).decode('utf-8')
            if response_data:
                return json.loads(response_data)
        except Exception as e:
            logger.error(f"Communication error: {e}")
            self.connected = False
        
        return None
    
    def disconnect(self) -> None:
        """Disconnect from host"""
        try:
            if self.socket:
                self.socket.close()
            self.connected = False
            logger.info("Disconnected from host")
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")


class DataWorker(QObject):
    """Worker thread for fetching data from host"""
    
    # Signals
    status_updated = pyqtSignal(dict)
    contacts_updated = pyqtSignal(dict)
    messages_updated = pyqtSignal(dict)
    connection_changed = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.connection = HostConnection()
        self.running = False
    
    def run(self) -> None:
        """Main update loop"""
        self.running = True
        
        while self.running:
            # Ensure connection
            if not self.connection.connected:
                self.connection.connect()
                self.connection_changed.emit(self.connection.connected)
            
            if self.connection.connected:
                # Fetch status
                status = self.connection.send_request({"type": "get_status"})
                if status:
                    self.status_updated.emit(status)
                
                # Fetch contacts
                contacts = self.connection.send_request({"type": "get_contacts"})
                if contacts:
                    self.contacts_updated.emit(contacts)
                
                # Fetch messages
                messages = self.connection.send_request({"type": "get_messages"})
                if messages:
                    self.messages_updated.emit(messages)
            
            # Wait before next update
            threading.Event().wait(UPDATE_INTERVAL / 1000)
    
    def stop(self) -> None:
        """Stop worker thread"""
        self.running = False
        self.connection.disconnect()


# ============================================================================
# Main UI
# ============================================================================

class SBMSControlCenter(QMainWindow):
    """Main SBMS Control Center window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SBMS Control Center - Samsung Bluetooth Message Service")
        self.setGeometry(100, 100, 1200, 800)
        
        self.worker = DataWorker()
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        
        # Connect signals
        self.worker_thread.started.connect(self.worker.run)
        self.worker.status_updated.connect(self._on_status_updated)
        self.worker.contacts_updated.connect(self._on_contacts_updated)
        self.worker.messages_updated.connect(self._on_messages_updated)
        self.worker.connection_changed.connect(self._on_connection_changed)
        
        self._init_ui()
        self._start_worker()
    
    def _init_ui(self) -> None:
        """Initialize UI components"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.connection_label = QLabel("Disconnected")
        self.status_bar.addPermanentWidget(self.connection_label)
        
        # Tabs
        tabs = QTabWidget()
        
        # Dashboard tab
        tabs.addTab(self._create_dashboard_tab(), "Dashboard")
        
        # Contacts tab
        tabs.addTab(self._create_contacts_tab(), "Contacts")
        
        # Messages tab
        tabs.addTab(self._create_messages_tab(), "Messages")
        
        # Devices tab
        tabs.addTab(self._create_devices_tab(), "Devices")
        
        layout.addWidget(tabs)
    
    def _create_dashboard_tab(self) -> QWidget:
        """Create dashboard tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Status grid
        h_layout = QHBoxLayout()
        
        # Contacts count
        self.contacts_count_label = QLabel("Contacts: 0")
        self.contacts_count_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        h_layout.addWidget(self.contacts_count_label)
        
        # Messages count
        self.messages_count_label = QLabel("Messages: 0")
        self.messages_count_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        h_layout.addWidget(self.messages_count_label)
        
        # Last update
        self.last_update_label = QLabel("Last update: Never")
        h_layout.addWidget(self.last_update_label)
        
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        # System log
        log_label = QLabel("System Log:")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        return widget
    
    def _create_contacts_tab(self) -> QWidget:
        """Create contacts tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter name or phone...")
        search_layout.addWidget(self.search_input)
        search_button = QPushButton("Search")
        search_button.clicked.connect(self._search_contacts)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)
        
        # Contacts table
        self.contacts_table = QTableWidget()
        self.contacts_table.setColumnCount(4)
        self.contacts_table.setHorizontalHeaderLabels(["Name", "Phone", "Added", "Last Contact"])
        layout.addWidget(self.contacts_table)
        
        return widget
    
    def _create_messages_tab(self) -> QWidget:
        """Create messages tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Message compose
        compose_label = QLabel("New Message:")
        compose_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(compose_label)
        
        compose_layout = QFormLayout()
        
        self.recipient_input = QLineEdit()
        self.recipient_input.setPlaceholderText("Enter recipient phone number")
        compose_layout.addRow("To:", self.recipient_input)
        
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Enter message text")
        self.message_input.setMaximumHeight(80)
        compose_layout.addRow("Message:", self.message_input)
        
        send_button = QPushButton("Send Message")
        send_button.clicked.connect(self._send_message)
        compose_layout.addRow("", send_button)
        
        layout.addLayout(compose_layout)
        
        # Message log
        log_label = QLabel("Message History:")
        log_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(log_label)
        
        self.messages_table = QTableWidget()
        self.messages_table.setColumnCount(6)
        self.messages_table.setHorizontalHeaderLabels(
            ["ID", "To", "Text", "Status", "Time", "Retries"]
        )
        layout.addWidget(self.messages_table)
        
        return widget
    
    def _create_devices_tab(self) -> QWidget:
        """Create devices tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Device status
        status_label = QLabel("Connected Devices:")
        status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(status_label)
        
        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(3)
        self.devices_table.setHorizontalHeaderLabels(["Device", "Status", "Last Seen"])
        layout.addWidget(self.devices_table)
        
        # Device info
        info_label = QLabel("Device Information:")
        info_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(info_label)
        
        self.device_info_text = QTextEdit()
        self.device_info_text.setReadOnly(True)
        self.device_info_text.setMaximumHeight(150)
        layout.addWidget(self.device_info_text)
        
        return widget
    
    # Event handlers
    
    def _on_status_updated(self, status: Dict) -> None:
        """Handle status update from host"""
        self.contacts_count_label.setText(f"Contacts: {status.get('contacts_count', 0)}")
        self.messages_count_label.setText(f"Messages: {status.get('messages_count', 0)}")
        self.last_update_label.setText(
            f"Last update: {datetime.now().strftime('%H:%M:%S')}"
        )
        self._log(f"Status updated: {status.get('contacts_count', 0)} contacts, {status.get('messages_count', 0)} messages")
    
    def _on_contacts_updated(self, contacts: Dict) -> None:
        """Handle contacts update from host"""
        data = contacts.get('data', {})
        self.contacts_table.setRowCount(len(data))
        
        for row, (phone, contact_info) in enumerate(data.items()):
            self.contacts_table.setItem(row, 0, QTableWidgetItem(contact_info.get('name', '')))
            self.contacts_table.setItem(row, 1, QTableWidgetItem(phone))
            self.contacts_table.setItem(row, 2, QTableWidgetItem(contact_info.get('added', '')[:10]))
            self.contacts_table.setItem(row, 3, QTableWidgetItem(contact_info.get('last_contact', 'Never')[:10] if contact_info.get('last_contact') else 'Never'))
        
        self._log(f"Contacts updated: {len(data)} total")
    
    def _on_messages_updated(self, messages: Dict) -> None:
        """Handle messages update from host"""
        data = messages.get('data', {})
        self.messages_table.setRowCount(len(data))
        
        for row, (msg_id, msg_info) in enumerate(data.items()):
            self.messages_table.setItem(row, 0, QTableWidgetItem(msg_id))
            self.messages_table.setItem(row, 1, QTableWidgetItem(msg_info.get('to_number', '')))
            self.messages_table.setItem(row, 2, QTableWidgetItem(msg_info.get('text', '')[:30]))
            
            status = msg_info.get('status', 'unknown')
            status_item = QTableWidgetItem(status)
            if status == 'delivered':
                status_item.setBackground(QColor(144, 238, 144))  # Light green
            elif status == 'failed':
                status_item.setBackground(QColor(255, 160, 160))  # Light red
            elif status == 'pending':
                status_item.setBackground(QColor(255, 255, 153))  # Light yellow
            
            self.messages_table.setItem(row, 3, status_item)
            self.messages_table.setItem(row, 4, QTableWidgetItem(msg_info.get('timestamp', '')[:16]))
            self.messages_table.setItem(row, 5, QTableWidgetItem(str(msg_info.get('retry_count', 0))))
    
    def _on_connection_changed(self, connected: bool) -> None:
        """Handle connection state change"""
        if connected:
            self.connection_label.setText("✓ Connected")
            self.connection_label.setStyleSheet("color: green; font-weight: bold;")
            self._log("Connected to SBMS Windows Host")
        else:
            self.connection_label.setText("✗ Disconnected")
            self.connection_label.setStyleSheet("color: red; font-weight: bold;")
            self._log("Disconnected from SBMS Windows Host")
    
    def _search_contacts(self) -> None:
        """Search contacts"""
        query = self.search_input.text().lower()
        
        for row in range(self.contacts_table.rowCount()):
            name = self.contacts_table.item(row, 0).text().lower()
            phone = self.contacts_table.item(row, 1).text().lower()
            
            if query in name or query in phone:
                self.contacts_table.showRow(row)
            else:
                self.contacts_table.hideRow(row)
    
    def _send_message(self) -> None:
        """Send new message"""
        to = self.recipient_input.text().strip()
        text = self.message_input.toPlainText().strip()
        
        if not to or not text:
            QMessageBox.warning(self, "Error", "Please enter recipient and message text")
            return
        
        # TODO: Send to Windows host
        QMessageBox.information(self, "Success", f"Message queued to {to}")
        self._log(f"Message sent to {to}: {text[:30]}...")
        
        self.recipient_input.clear()
        self.message_input.clear()
    
    def _log(self, message: str) -> None:
        """Add message to system log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        logger.info(message)
    
    def _start_worker(self) -> None:
        """Start worker thread"""
        self.worker_thread.start()
    
    def closeEvent(self, event) -> None:
        """Handle window close"""
        self.worker.stop()
        self.worker_thread.quit()
        self.worker_thread.wait()
        event.accept()


# ============================================================================
# Entry Point
# ============================================================================

def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    window = SBMSControlCenter()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
