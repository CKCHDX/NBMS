package com.oscyra.sbms;

import android.Manifest;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.ContactsContract;
import android.text.Editable;
import android.text.TextWatcher;
import android.util.Log;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.room.Room;

import com.oscyra.sbms.bluetooth.BluetoothManager;
import com.oscyra.sbms.data.AppDatabase;
import com.oscyra.sbms.data.Contact;
import com.oscyra.sbms.data.Message;
import com.oscyra.sbms.ui.ContactAdapter;
import com.oscyra.sbms.utils.SBMSMessageFormatter;

import java.util.ArrayList;
import java.util.List;

public class MainActivity extends AppCompatActivity {
    private static final String TAG = "SBMS_MainActivity";
    private static final int PERMISSION_REQUEST_CODE = 1001;

    private BluetoothAdapter bluetoothAdapter;
    private BluetoothManager bluetoothManager;
    private AppDatabase database;
    private Handler mainHandler;

    // UI Components
    private EditText messageInput;
    private EditText contactSearch;
    private ListView contactsList;
    private Button sendButton;
    private Button connectButton;
    private TextView deviceStatus;
    private TextView messageCounter;
    private TextView selectedContactDisplay;

    // Data
    private ArrayList<Contact> allContacts = new ArrayList<>();
    private ArrayList<Contact> filteredContacts = new ArrayList<>();
    private ContactAdapter contactAdapter;
    private Contact selectedContact = null;

    private BroadcastReceiver bluetoothReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String action = intent.getAction();
            if (BluetoothAdapter.ACTION_STATE_CHANGED.equals(action)) {
                int state = intent.getIntExtra(BluetoothAdapter.EXTRA_STATE, BluetoothAdapter.ERROR);
                updateBluetoothStatus(state);
            } else if (BluetoothDevice.ACTION_FOUND.equals(action)) {
                BluetoothDevice device = intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE);
                Log.d(TAG, "Device found: " + device.getName());
            }
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        mainHandler = new Handler(Looper.getMainLooper());
        initializeDatabase();
        initializeBluetoothAdapter();
        initializeUIComponents();
        loadContacts();
        registerBluetoothReceiver();
        checkPermissions();
    }

    private void initializeDatabase() {
        database = Room.databaseBuilder(getApplicationContext(), AppDatabase.class, "sbms_db")
                .fallbackToDestructiveMigration()
                .build();
    }

    private void initializeBluetoothAdapter() {
        bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        if (bluetoothAdapter == null) {
            Toast.makeText(this, "Bluetooth not supported", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }
        bluetoothManager = new BluetoothManager(this, bluetoothAdapter, new BluetoothManager.BluetoothCallback() {
            @Override
            public void onConnectionStateChanged(int state, String message) {
                mainHandler.post(() -> updateConnectionStatus(state, message));
            }

            @Override
            public void onMessageReceived(Message message) {
                mainHandler.post(() -> handleReceivedMessage(message));
            }

            @Override
            public void onError(String errorMessage) {
                mainHandler.post(() -> showError(errorMessage));
            }
        });
    }

    private void initializeUIComponents() {
        messageInput = findViewById(R.id.message_input);
        contactSearch = findViewById(R.id.contact_search);
        contactsList = findViewById(R.id.contacts_list);
        sendButton = findViewById(R.id.send_button);
        connectButton = findViewById(R.id.connect_button);
        deviceStatus = findViewById(R.id.device_status);
        messageCounter = findViewById(R.id.message_counter);
        selectedContactDisplay = findViewById(R.id.selected_contact_display);

        contactAdapter = new ContactAdapter(this, filteredContacts);
        contactsList.setAdapter(contactAdapter);

        // Message input listener
        messageInput.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                updateMessageCounter(s.length());
            }

            @Override
            public void afterTextChanged(Editable s) {}
        });

        // Contact search listener
        contactSearch.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                filterContacts(s.toString());
            }

            @Override
            public void afterTextChanged(Editable s) {}
        });

        // Contact selection listener
        contactsList.setOnItemClickListener((parent, view, position, id) -> {
            selectedContact = filteredContacts.get(position);
            selectedContactDisplay.setText("To: " + selectedContact.getDisplayName() + " (" + selectedContact.getPhoneNumber() + ")");
            selectedContactDisplay.setVisibility(View.VISIBLE);
            sendButton.setEnabled(true);
        });

        // Send button
        sendButton.setOnClickListener(v -> sendMessage());
        sendButton.setEnabled(false);

        // Connect button
        connectButton.setOnClickListener(v -> initiateConnection());
    }

    private void loadContacts() {
        new Thread(() -> {
            List<Contact> contacts = database.contactDao().getAllContacts();
            mainHandler.post(() -> {
                allContacts.clear();
                allContacts.addAll(contacts);
                filterContacts("");
            });
        }).start();
    }

    private void filterContacts(String query) {
        filteredContacts.clear();
        if (query.isEmpty()) {
            filteredContacts.addAll(allContacts);
        } else {
            String lowerQuery = query.toLowerCase();
            for (Contact contact : allContacts) {
                if (contact.getDisplayName().toLowerCase().contains(lowerQuery) ||
                    contact.getPhoneNumber().contains(query)) {
                    filteredContacts.add(contact);
                }
            }
        }
        contactAdapter.notifyDataSetChanged();
    }

    private void updateMessageCounter(int length) {
        messageCounter.setText(length + "/160 chars");
        if (length > 160) {
            messageCounter.setTextColor(ContextCompat.getColor(this, R.color.error_red));
        } else {
            messageCounter.setTextColor(ContextCompat.getColor(this, R.color.text_secondary));
        }
    }

    private void sendMessage() {
        if (selectedContact == null) {
            showError("Select a contact first");
            return;
        }

        String messageText = messageInput.getText().toString().trim();
        if (messageText.isEmpty()) {
            showError("Message cannot be empty");
            return;
        }

        if (messageText.length() > 160) {
            showError("Message exceeds 160 characters");
            return;
        }

        // Format message as vCard
        String vCardMessage = SBMSMessageFormatter.createVCardMessage(
                selectedContact.getPhoneNumber(),
                messageText,
                generateUUID(selectedContact.getPhoneNumber() + messageText)
        );

        // Send via Bluetooth
        bluetoothManager.sendMessage(selectedContact.getPhoneNumber(), vCardMessage, result -> {
            mainHandler.post(() -> {
                if (result) {
                    Toast.makeText(MainActivity.this, "Message sent", Toast.LENGTH_SHORT).show();
                    messageInput.setText("");
                    selectedContact = null;
                    selectedContactDisplay.setVisibility(View.GONE);
                    sendButton.setEnabled(false);
                } else {
                    showError("Failed to send message");
                }
            });
        });
    }

    private void initiateConnection() {
        if (!bluetoothAdapter.isEnabled()) {
            Intent enableBtIntent = new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE);
            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED) {
                ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.BLUETOOTH_CONNECT}, PERMISSION_REQUEST_CODE);
                return;
            }
            startActivityForResult(enableBtIntent, 1);
        } else {
            bluetoothManager.connectToE1310E();
        }
    }

    private void updateConnectionStatus(int state, String message) {
        connectButton.setEnabled(state != BluetoothManager.STATE_CONNECTED);
        deviceStatus.setText(message);
    }

    private void handleReceivedMessage(Message message) {
        // Save message to database
        new Thread(() -> database.messageDao().insert(message)).start();
        Toast.makeText(this, "Message received from " + message.getSenderPhoneNumber(), Toast.LENGTH_SHORT).show();
    }

    private void updateBluetoothStatus(int state) {
        String status;
        switch (state) {
            case BluetoothAdapter.STATE_ON:
                status = "Bluetooth: Ready";
                connectButton.setEnabled(true);
                break;
            case BluetoothAdapter.STATE_OFF:
                status = "Bluetooth: Off";
                connectButton.setEnabled(false);
                break;
            case BluetoothAdapter.STATE_TURNING_ON:
                status = "Bluetooth: Turning On...";
                break;
            case BluetoothAdapter.STATE_TURNING_OFF:
                status = "Bluetooth: Turning Off...";
                break;
            default:
                status = "Bluetooth: Unknown";
        }
        deviceStatus.setText(status);
    }

    private void checkPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            String[] permissions = {
                    Manifest.permission.BLUETOOTH_SCAN,
                    Manifest.permission.BLUETOOTH_CONNECT,
                    Manifest.permission.READ_CONTACTS,
                    Manifest.permission.SEND_SMS
            };
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_SCAN) != PackageManager.PERMISSION_GRANTED) {
                ActivityCompat.requestPermissions(this, permissions, PERMISSION_REQUEST_CODE);
            }
        }
    }

    private void registerBluetoothReceiver() {
        IntentFilter filter = new IntentFilter();
        filter.addAction(BluetoothAdapter.ACTION_STATE_CHANGED);
        filter.addAction(BluetoothDevice.ACTION_FOUND);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            registerReceiver(bluetoothReceiver, filter, Context.RECEIVER_EXPORTED);
        } else {
            registerReceiver(bluetoothReceiver, filter);
        }
    }

    private void showError(String message) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
        Log.e(TAG, message);
    }

    private String generateUUID(String seed) {
        return String.format("%08X",
                Math.abs(seed.hashCode()));
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        try {
            unregisterReceiver(bluetoothReceiver);
        } catch (IllegalArgumentException e) {
            Log.e(TAG, "Bluetooth receiver not registered");
        }
        if (bluetoothManager != null) {
            bluetoothManager.disconnect();
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST_CODE) {
            boolean allGranted = true;
            for (int result : grantResults) {
                if (result != PackageManager.PERMISSION_GRANTED) {
                    allGranted = false;
                    break;
                }
            }
            if (allGranted) {
                checkPermissions();
            }
        }
    }
}
