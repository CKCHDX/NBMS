#!/usr/bin/env python3
"""
SBMS Test Device Client

Simulates a Bluetooth device (Z Fold 6 or E1310E) connecting to SBMS Windows Host.
Uses TCP fallback on port 5555 for easy testing without real Bluetooth hardware.

Author: Alex Jonsson
Location: Kista, Sweden
Date: December 2025
"""

import json
import socket
import sys
import time
from datetime import datetime
from typing import Dict, Optional

# ============================================================================
# Configuration
# ============================================================================

HOST_IP = "127.0.0.1"
BLUETOOTH_PORT = 5555  # TCP fallback port
SOCKET_TIMEOUT = 5  # seconds

# ============================================================================
# Device Client
# ============================================================================

class TestDeviceClient:
    """Test device client for SBMS"""
    
    def __init__(self, device_name: str = "TestDevice"):
        self.device_name = device_name
        self.socket = None
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to SBMS host"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(SOCKET_TIMEOUT)
            self.socket.connect((HOST_IP, BLUETOOTH_PORT))
            self.connected = True
            print(f"[OK] Connected to {HOST_IP}:{BLUETOOTH_PORT}")
            
            # Identify ourselves to the host
            self.identify()
            return True
        
        except Exception as e:
            print(f"[ERROR] Failed to connect: {e}")
            self.connected = False
            return False
    
    def send_message(self, msg: Dict) -> Optional[Dict]:
        """Send message to host and receive response"""
        try:
            if not self.connected:
                print("[ERROR] Not connected to host")
                return None
            
            # Send
            data = json.dumps(msg).encode('utf-8')
            self.socket.sendall(data)
            print(f"[SEND] {msg}")
            
            # Receive
            response_data = self.socket.recv(4096).decode('utf-8')
            response = json.loads(response_data)
            print(f"[RECV] {response}")
            return response
        
        except Exception as e:
            print(f"[ERROR] Communication failed: {e}")
            self.connected = False
            return None
    
    def identify(self) -> Optional[Dict]:
        """Identify device to host"""
        msg = {
            "type": "identify",
            "device": self.device_name
        }
        return self.send_message(msg)
    
    def get_contacts(self) -> Optional[Dict]:
        """Request contacts from host"""
        msg = {"type": "get_contacts"}
        return self.send_message(msg)
    
    def sync_contacts(self, contacts: list) -> Optional[Dict]:
        """Sync contacts to host"""
        msg = {
            "type": "sync_contacts",
            "contacts": contacts
        }
        return self.send_message(msg)
    
    def send_sms(self, to_number: str, text: str) -> Optional[Dict]:
        """Send SMS through host"""
        msg_id = f"msg_{int(time.time() * 1000)}"
        msg = {
            "type": "send_message",
            "id": msg_id,
            "to": to_number,
            "text": text
        }
        return self.send_message(msg)
    
    def report_sms_status(self, msg_id: str, status: str) -> Optional[Dict]:
        """Report SMS delivery status"""
        msg = {
            "type": "sms_status",
            "id": msg_id,
            "status": status
        }
        return self.send_message(msg)
    
    def ping(self) -> Optional[Dict]:
        """Ping host"""
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
        print("[INFO] Disconnected from host")


# ============================================================================
# Interactive CLI
# ============================================================================

def show_menu():
    """Display interactive menu"""
    print("\n" + "="*60)
    print("SBMS Test Device CLI")
    print("="*60)
    print("1. Connect to host")
    print("2. Identify device")
    print("3. Get contacts")
    print("4. Sync contacts to host")
    print("5. Send SMS")
    print("6. Report SMS status")
    print("7. Ping host")
    print("8. Disconnect")
    print("9. Exit")
    print("="*60)


def main():
    """Main CLI loop"""
    device = TestDeviceClient("Z Fold 6")
    
    print("\nSBMS Test Device Client")
    print(f"Target: {HOST_IP}:{BLUETOOTH_PORT}")
    print("Type 'help' or '9' to see commands\n")
    
    while True:
        try:
            show_menu()
            choice = input("\nSelect option: ").strip()
            
            if choice == "1":
                device.connect()
            
            elif choice == "2":
                if device.connected:
                    device.identify()
                else:
                    print("[ERROR] Not connected. Connect first.")
            
            elif choice == "3":
                if device.connected:
                    response = device.get_contacts()
                    if response and 'data' in response:
                        contacts = response['data']
                        if contacts:
                            print("\n[CONTACTS]")
                            for phone, info in contacts.items():
                                print(f"  {info['name']} <{phone}>")
                        else:
                            print("[INFO] No contacts on host")
                else:
                    print("[ERROR] Not connected. Connect first.")
            
            elif choice == "4":
                if device.connected:
                    # Example: sync some test contacts
                    test_contacts = [
                        {"phone": "+46701234567", "name": "Alice Andersson"},
                        {"phone": "+46702345678", "name": "Bob Bergstrom"},
                        {"phone": "+46703456789", "name": "Charlie Carlson"}
                    ]
                    print(f"\n[INFO] Syncing {len(test_contacts)} contacts...")
                    for contact in test_contacts:
                        print(f"  - {contact['name']} ({contact['phone']})")
                    device.sync_contacts(test_contacts)
                else:
                    print("[ERROR] Not connected. Connect first.")
            
            elif choice == "5":
                if device.connected:
                    to_number = input("Enter recipient phone: ").strip()
                    text = input("Enter message text: ").strip()
                    if to_number and text:
                        device.send_sms(to_number, text)
                    else:
                        print("[ERROR] Phone and text required")
                else:
                    print("[ERROR] Not connected. Connect first.")
            
            elif choice == "6":
                if device.connected:
                    msg_id = input("Enter message ID: ").strip()
                    status = input("Enter status (pending/delivered/failed): ").strip()
                    if msg_id and status in ["pending", "delivered", "failed"]:
                        device.report_sms_status(msg_id, status)
                    else:
                        print("[ERROR] Invalid input")
                else:
                    print("[ERROR] Not connected. Connect first.")
            
            elif choice == "7":
                if device.connected:
                    device.ping()
                else:
                    print("[ERROR] Not connected. Connect first.")
            
            elif choice == "8":
                device.disconnect()
            
            elif choice == "9" or choice.lower() == "exit":
                if device.connected:
                    device.disconnect()
                print("\n[INFO] Exiting...")
                break
            
            else:
                print("[ERROR] Invalid option")
        
        except KeyboardInterrupt:
            print("\n\n[INFO] Interrupted by user")
            if device.connected:
                device.disconnect()
            break
        
        except Exception as e:
            print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
