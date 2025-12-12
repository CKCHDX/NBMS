package com.oscyra.sbms.bluetooth;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.content.Context;
import android.util.Log;

import com.oscyra.sbms.data.Message;
import com.oscyra.sbms.utils.SBMSMessageFormatter;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.UUID;

public class BluetoothManager {
    private static final String TAG = "SBMS_BluetoothManager";
    public static final int STATE_IDLE = 0;
    public static final int STATE_CONNECTING = 1;
    public static final int STATE_CONNECTED = 2;
    public static final int STATE_ERROR = 3;

    private static final UUID OBEX_OBJECT_PUSH_PROFILE = UUID.fromString("00001105-0000-1000-8000-00805f9b34fb");
    private static final UUID RFCOMM_UUID = UUID.fromString("00001101-0000-1000-8000-00805f9b34fb");

    private BluetoothAdapter bluetoothAdapter;
    private BluetoothSocket bluetoothSocket;
    private InputStream inputStream;
    private OutputStream outputStream;
    private int connectionState = STATE_IDLE;
    private BluetoothCallback bluetoothCallback;
    private Context context;

    private Thread listenerThread;
    private volatile boolean isListening = false;

    public interface BluetoothCallback {
        void onConnectionStateChanged(int state, String message);
        void onMessageReceived(Message message);
        void onError(String errorMessage);
    }

    public BluetoothManager(Context context, BluetoothAdapter adapter, BluetoothCallback callback) {
        this.context = context;
        this.bluetoothAdapter = adapter;
        this.bluetoothCallback = callback;
    }

    public void connectToE1310E() {
        new Thread(() -> {
            try {
                setConnectionState(STATE_CONNECTING, "Connecting to E1310E...");

                // Get E1310E device (you should store the MAC address)
                String e1310eMac = getE1310EMacAddress(); // Implement this based on your setup
                if (e1310eMac == null) {
                    throw new IOException("E1310E device not found");
                }

                BluetoothDevice device = bluetoothAdapter.getRemoteDevice(e1310eMac);

                // Create socket using RFCOMM UUID
                bluetoothSocket = device.createRfcommSocketToServiceRecord(RFCOMM_UUID);
                if (bluetoothSocket == null) {
                    bluetoothSocket = device.createRfcommSocketToServiceRecord(OBEX_OBJECT_PUSH_PROFILE);
                }

                // Connect
                bluetoothSocket.connect();

                inputStream = bluetoothSocket.getInputStream();
                outputStream = bluetoothSocket.getOutputStream();

                setConnectionState(STATE_CONNECTED, "Connected to E1310E");

                // Start listening for incoming messages
                startListening();

            } catch (IOException e) {
                Log.e(TAG, "Connection failed", e);
                setConnectionState(STATE_ERROR, "Connection failed: " + e.getMessage());
                bluetoothCallback.onError("Failed to connect: " + e.getMessage());
                disconnect();
            }
        }).start();
    }

    public void sendMessage(String recipientPhone, String vCardMessage, SendCallback callback) {
        new Thread(() -> {
            try {
                if (outputStream == null) {
                    callback.onResult(false);
                    return;
                }

                byte[] messageBytes = vCardMessage.getBytes("UTF-8");
                outputStream.write(messageBytes);
                outputStream.flush();

                Log.d(TAG, "Message sent to " + recipientPhone);
                callback.onResult(true);

            } catch (IOException e) {
                Log.e(TAG, "Error sending message", e);
                callback.onResult(false);
                bluetoothCallback.onError("Send failed: " + e.getMessage());
            }
        }).start();
    }

    private void startListening() {
        if (isListening) {
            return;
        }

        isListening = true;
        listenerThread = new Thread(() -> {
            byte[] buffer = new byte[1024];
            int bytes;

            while (isListening) {
                try {
                    if (inputStream == null) {
                        break;
                    }

                    bytes = inputStream.read(buffer);
                    if (bytes > 0) {
                        String receivedData = new String(buffer, 0, bytes, "UTF-8");
                        Message message = SBMSMessageFormatter.parseVCardMessage(receivedData);
                        if (message != null) {
                            bluetoothCallback.onMessageReceived(message);
                        }
                    }
                } catch (IOException e) {
                    if (isListening) {
                        Log.e(TAG, "Error reading from input stream", e);
                        bluetoothCallback.onError("Connection lost: " + e.getMessage());
                        disconnect();
                    }
                    break;
                }
            }
        });
        listenerThread.start();
    }

    public void disconnect() {
        isListening = false;
        try {
            if (inputStream != null) {
                inputStream.close();
            }
            if (outputStream != null) {
                outputStream.close();
            }
            if (bluetoothSocket != null) {
                bluetoothSocket.close();
            }
        } catch (IOException e) {
            Log.e(TAG, "Error closing connection", e);
        }
        setConnectionState(STATE_IDLE, "Disconnected");
    }

    private void setConnectionState(int state, String message) {
        this.connectionState = state;
        bluetoothCallback.onConnectionStateChanged(state, message);
    }

    public int getConnectionState() {
        return connectionState;
    }

    private String getE1310EMacAddress() {
        // TODO: Implement device discovery or use stored MAC address
        // For now, return a placeholder that you should replace
        return "E1:31:0E:12:34:56"; // Replace with actual E1310E MAC
    }

    public interface SendCallback {
        void onResult(boolean success);
    }
}
