package com.oscyra.sbms.android;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import com.oscyra.sbms.android.bluetooth.OppServerService;
import com.oscyra.sbms.android.messaging.ConversationListActivity;

/**
 * Main entry point for SBMS Android application.
 * Handles permission requests and navigation to messaging UI.
 */
public class MainActivity extends AppCompatActivity {
    
    private static final String TAG = "SBMS.MainActivity";
    private static final int PERMISSION_REQUEST_CODE = 100;
    
    private final String[] REQUIRED_PERMISSIONS = {
            Manifest.permission.BLUETOOTH,
            Manifest.permission.BLUETOOTH_ADMIN,
            Manifest.permission.SEND_SMS,
            Manifest.permission.RECEIVE_SMS,
            Manifest.permission.READ_SMS,
            Manifest.permission.READ_CONTACTS,
            Manifest.permission.READ_EXTERNAL_STORAGE,
            Manifest.permission.WRITE_EXTERNAL_STORAGE,
            Manifest.permission.READ_PHONE_STATE
    };
    
    private TextView statusTextView;
    private Button startButton;
    private Button conversationsButton;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        Log.d(TAG, "MainActivity created");
        
        // Initialize views
        statusTextView = findViewById(R.id.status_text);
        startButton = findViewById(R.id.btn_start_opp_server);
        conversationsButton = findViewById(R.id.btn_open_conversations);
        
        // Request permissions
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            // Android 12+: additional Bluetooth permissions
            String[] s12Permissions = {
                    Manifest.permission.BLUETOOTH_CONNECT,
                    Manifest.permission.BLUETOOTH_ADVERTISE,
                    Manifest.permission.BLUETOOTH_SCAN
            };
            requestPermissions(s12Permissions, PERMISSION_REQUEST_CODE);
        }
        
        if (!hasAllPermissions()) {
            requestPermissions(REQUIRED_PERMISSIONS, PERMISSION_REQUEST_CODE);
        } else {
            updateStatus("✓ All permissions granted");
        }
        
        // Setup button listeners
        startButton.setOnClickListener(v -> startOppServer());
        conversationsButton.setOnClickListener(v -> openConversations());
    }
    
    @Override
    protected void onStart() {
        super.onStart();
        Log.d(TAG, "MainActivity started");
        
        // Auto-start OPP server
        if (hasAllPermissions()) {
            startOppServer();
        }
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        Log.d(TAG, "MainActivity destroyed");
    }
    
    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions,
                                           @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        
        if (requestCode == PERMISSION_REQUEST_CODE) {
            if (hasAllPermissions()) {
                updateStatus("✓ All permissions granted");
                startOppServer();
            } else {
                updateStatus("✗ Missing required permissions");
                Toast.makeText(this, "SBMS requires Bluetooth and SMS permissions", Toast.LENGTH_LONG).show();
            }
        }
    }
    
    private void startOppServer() {
        Log.d(TAG, "Starting OPP server service");
        Intent serviceIntent = new Intent(this, OppServerService.class);
        startService(serviceIntent);
        updateStatus("✓ OPP Server started (listening for E1310E messages)");
    }
    
    private void openConversations() {
        Intent intent = new Intent(this, ConversationListActivity.class);
        startActivity(intent);
    }
    
    private void updateStatus(String message) {
        runOnUiThread(() -> {
            statusTextView.setText(message);
            Log.d(TAG, message);
        });
    }
    
    private boolean hasAllPermissions() {
        for (String permission : REQUIRED_PERMISSIONS) {
            if (ContextCompat.checkSelfPermission(this, permission)
                    != PackageManager.PERMISSION_GRANTED) {
                return false;
            }
        }
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT)
                    != PackageManager.PERMISSION_GRANTED) {
                return false;
            }
        }
        
        return true;
    }
}
