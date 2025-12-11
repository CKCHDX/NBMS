package com.ckcdhx.sbms

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.Button
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.ckcdhx.sbms.service.SBMSBluetoothService
import kotlinx.coroutines.launch
import timber.log.Timber
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Main Activity for SBMS (Samsung Bluetooth Message Service)
 *
 * Displays connection status, message history, and permissions status
 * Also handles permission requests for Bluetooth, SMS, and file access
 */
class MainActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "SBMSMainActivity"
        private const val PERMISSION_REQUEST_CODE = 100
    }

    private var isServiceRunning = false
    
    // UI Views
    private lateinit var textServiceStatus: TextView
    private lateinit var textPermissionStatus: TextView
    private lateinit var buttonStartService: Button
    private lateinit var buttonStopService: Button
    private lateinit var buttonOpenSettings: Button
    private lateinit var buttonClearLogs: Button
    private lateinit var textLogs: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // Initialize Timber logging
        if (BuildConfig.DEBUG) {
            Timber.plant(Timber.DebugTree())
        }
        
        // Find views
        initializeViews()
        
        // Setup
        setupUI()
        checkAndRequestPermissions()
        startSBMSService()
    }

    override fun onResume() {
        super.onResume()
        updateServiceStatus()
    }

    /**
     * Initialize all UI views
     */
    private fun initializeViews() {
        textServiceStatus = findViewById(R.id.textServiceStatus)
        textPermissionStatus = findViewById(R.id.textPermissionStatus)
        buttonStartService = findViewById(R.id.buttonStartService)
        buttonStopService = findViewById(R.id.buttonStopService)
        buttonOpenSettings = findViewById(R.id.buttonOpenSettings)
        buttonClearLogs = findViewById(R.id.buttonClearLogs)
        textLogs = findViewById(R.id.textLogs)
    }

    /**
     * Setup UI elements and listeners
     */
    private fun setupUI() {
        buttonStartService.setOnClickListener { startSBMSService() }
        buttonStopService.setOnClickListener { stopSBMSService() }
        buttonOpenSettings.setOnClickListener { openBluetoothSettings() }
        buttonClearLogs.setOnClickListener { clearLogs() }
    }

    /**
     * Check and request necessary permissions
     */
    private fun checkAndRequestPermissions() {
        val requiredPermissions = mutableListOf(
            Manifest.permission.BLUETOOTH,
            Manifest.permission.BLUETOOTH_ADMIN,
            Manifest.permission.SEND_SMS,
            Manifest.permission.READ_SMS,
            Manifest.permission.RECEIVE_SMS,
            Manifest.permission.READ_CONTACTS,
            Manifest.permission.READ_EXTERNAL_STORAGE,
            Manifest.permission.WRITE_EXTERNAL_STORAGE
        )

        // Android 12+ requires BLUETOOTH_SCAN and BLUETOOTH_CONNECT
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            requiredPermissions.add(Manifest.permission.BLUETOOTH_SCAN)
            requiredPermissions.add(Manifest.permission.BLUETOOTH_CONNECT)
        }

        // Android 13+ requires more granular permission
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            requiredPermissions.add(Manifest.permission.READ_MEDIA_AUDIO)
        }

        val missingPermissions = requiredPermissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (missingPermissions.isNotEmpty()) {
            Timber.d("Requesting permissions: $missingPermissions")
            ActivityCompat.requestPermissions(
                this,
                missingPermissions.toTypedArray(),
                PERMISSION_REQUEST_CODE
            )
        } else {
            Timber.i("All permissions already granted")
            updatePermissionStatus(granted = true)
        }
    }

    /**
     * Handle permission request results
     */
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        
        if (requestCode == PERMISSION_REQUEST_CODE) {
            val allGranted = grantResults.all { it == PackageManager.PERMISSION_GRANTED }
            
            if (allGranted) {
                Timber.i("All permissions granted")
                updatePermissionStatus(granted = true)
                startSBMSService()
            } else {
                Timber.w("Some permissions denied")
                updatePermissionStatus(granted = false)
            }
        }
    }

    /**
     * Start SBMS Bluetooth Service
     */
    private fun startSBMSService() {
        try {
            val serviceIntent = Intent(this, SBMSBluetoothService::class.java)
            
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                startForegroundService(serviceIntent)
            } else {
                startService(serviceIntent)
            }
            
            isServiceRunning = true
            Timber.i("SBMS Service started")
            updateServiceStatus()
        } catch (e: Exception) {
            Timber.e(e, "Error starting service")
            addLog("Error starting service: ${e.message}")
        }
    }

    /**
     * Stop SBMS Bluetooth Service
     */
    private fun stopSBMSService() {
        try {
            val serviceIntent = Intent(this, SBMSBluetoothService::class.java)
            stopService(serviceIntent)
            
            isServiceRunning = false
            Timber.i("SBMS Service stopped")
            updateServiceStatus()
        } catch (e: Exception) {
            Timber.e(e, "Error stopping service")
            addLog("Error stopping service: ${e.message}")
        }
    }

    /**
     * Update service status UI
     */
    private fun updateServiceStatus() {
        lifecycleScope.launch {
            if (isServiceRunning) {
                textServiceStatus.text = "\u2713 Running"
                textServiceStatus.setTextColor(getColor(android.R.color.holo_green_dark))
                buttonStartService.isEnabled = false
                buttonStopService.isEnabled = true
            } else {
                textServiceStatus.text = "\u2717 Stopped"
                textServiceStatus.setTextColor(getColor(android.R.color.holo_red_dark))
                buttonStartService.isEnabled = true
                buttonStopService.isEnabled = false
            }
        }
    }

    /**
     * Update permission status UI
     */
    private fun updatePermissionStatus(granted: Boolean) {
        if (granted) {
            textPermissionStatus.text = "\u2713 All permissions granted"
            textPermissionStatus.setTextColor(getColor(android.R.color.holo_green_dark))
        } else {
            textPermissionStatus.text = "\u2717 Some permissions missing"
            textPermissionStatus.setTextColor(getColor(android.R.color.holo_red_dark))
        }
    }

    /**
     * Open Bluetooth settings
     */
    private fun openBluetoothSettings() {
        val intent = Intent(android.provider.Settings.ACTION_BLUETOOTH_SETTINGS)
        startActivity(intent)
    }

    /**
     * Add log message to UI
     */
    private fun addLog(message: String) {
        val timestamp = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
            .format(Date())
        val logEntry = "[$timestamp] $message\n"
        
        textLogs.text = logEntry + textLogs.text
    }

    /**
     * Clear logs from UI
     */
    private fun clearLogs() {
        textLogs.text = ""
    }
}
