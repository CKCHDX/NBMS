package com.oscyra.sbms.bluetooth;

import java.io.*;
import javax.bluetooth.*;
import javax.microedition.io.*;

/**
 * Handles Bluetooth OPP (Object Push Profile) communication on E1310E
 */
public class BluetoothHandler {
    private static final String OBEX_UUID = "00001105-0000-1000-8000-00805f9b34fb";
    private StreamConnection connection;
    private DataInputStream inputStream;
    private DataOutputStream outputStream;
    
    public interface SendCallback {
        void onResult(boolean success);
    }

    public BluetoothHandler() {
    }

    public void sendMessage(String vCardMessage, SendCallback callback) {
        new Thread(new Runnable() {
            public void run() {
                try {
                    // Connect to paired phone device
                    String phoneAddress = discoverPhoneDevice();
                    if (phoneAddress == null) {
                        callback.onResult(false);
                        return;
                    }

                    // Create OPP connection string
                    String connectionString = "btspp://" + phoneAddress + ":" + OBEX_UUID + ";authenticate=false;encrypt=false;master=false";
                    connection = (StreamConnection) Connector.open(connectionString);
                    
                    outputStream = new DataOutputStream(connection.openOutputStream());
                    inputStream = new DataInputStream(connection.openInputStream());

                    // Send OBEX handshake
                    if (!performOBEXHandshake()) {
                        connection.close();
                        callback.onResult(false);
                        return;
                    }

                    // Send message via OBEX PUT
                    if (sendOBEXMessage(vCardMessage)) {
                        callback.onResult(true);
                    } else {
                        callback.onResult(false);
                    }

                    connection.close();
                } catch (IOException e) {
                    e.printStackTrace();
                    callback.onResult(false);
                }
            }
        }).start();
    }

    private String discoverPhoneDevice() throws IOException {
        // Search for discovered devices
        // In production, would use RemoteDevice enumeration
        // For now, assume paired device stored in config
        return "001D7E80A0B8"; // Replace with actual phone MAC discovery
    }

    private boolean performOBEXHandshake() throws IOException {
        // OBEX CONNECT command
        // 0x80 = OBEX CONNECT
        outputStream.writeByte(0x80);
        outputStream.writeByte(0x00); // Version
        outputStream.writeByte(0x00); // Flags
        outputStream.writeShort(0x0007); // Length
        outputStream.flush();

        // Read response
        byte response = inputStream.readByte();
        return response == 0xA0; // Success response
    }

    private boolean sendOBEXMessage(String vCardData) throws IOException {
        byte[] data = vCardData.getBytes("UTF-8");
        
        // OBEX PUT command
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        DataOutputStream dos = new DataOutputStream(baos);
        
        // Message filename header (0x01 = Count, followed by name)
        dos.writeByte(0x48); // Name header type
        dos.writeShort(data.length + 5);
        dos.writeBytes("message.vcd");
        
        // Message body
        dos.writeByte(0x49); // Body header
        dos.writeShort(data.length + 3);
        dos.write(data);
        
        // End of body
        dos.writeByte(0xC9);
        dos.writeShort(0x0003);
        
        byte[] payload = baos.toByteArray();
        
        // Send PUT request
        outputStream.writeByte(0x02); // PUT command
        outputStream.writeShort(payload.length + 3);
        outputStream.write(payload);
        outputStream.flush();
        
        // Read response
        byte response = inputStream.readByte();
        return response == 0xA0; // Success
    }

    public void disconnect() {
        try {
            if (connection != null) {
                connection.close();
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
