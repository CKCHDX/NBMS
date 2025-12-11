package com.ckchdx.sbms.service

import android.app.Service
import android.content.Intent
import android.content.IntentFilter
import android.os.IBinder
import android.os.Environment
import android.provider.DocumentsContract
import android.util.Log
import androidx.core.content.FileProvider
import com.ckchdx.sbms.model.SBMSMessage
import com.ckchdx.sbms.receiver.BluetoothFileReceiver
import com.ckchdx.sbms.util.SMSManager
import kotlinx.coroutines.*
import java.io.File
import java.nio.file.Files
import java.nio.file.StandardWatchEventKinds
import java.nio.file.WatchService

/**
 * SBMS Bluetooth Service
 *
 * This service monitors the Bluetooth OPP receive folder for incoming vCard files
 * containing X-SBMS-* properties. When a message is detected:
 *
 * 1. Parse the vCard to extract message details
 * 2. Show preview to user for confirmation
 * 3. Send actual SMS via Android SMS API
 * 4. Generate status response vCard
 * 5. Push response back to E1310E via Bluetooth OPP
 *
 * Typical paths:
 * - Android 10+: /sdcard/Download/Bluetooth/ or /sdcard/Android/media/.../Bluetooth/
 * - Older: /sdcard/Download/ or /sdcard/Bluetooth/
 */
class SBMSBluetoothService : Service() {

    companion object {
        private const val TAG = "SBMSBluetoothService"
        private const val POLL_INTERVAL_MS = 2000L

        // Possible Bluetooth OPP receive folders (platform dependent)
        private val BLUETOOTH_OPP_PATHS = listOf(
            "/sdcard/Download/Bluetooth",
            "/sdcard/Bluetooth",
            "/sdcard/Download",
            "/storage/emulated/0/Download/Bluetooth",
            "/storage/emulated/0/Bluetooth",
            "/storage/emulated/0/Download"
        )
    }

    private val serviceScope = CoroutineScope(Dispatchers.Default + Job())
    private val smsManager by lazy { SMSManager(this) }
    private var pollingJob: Job? = null
    private var lastProcessedFiles = mutableSetOf<String>()

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.i(TAG, "SBMS Bluetooth Service started")
        startBluetoothMonitoring()
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        Log.i(TAG, "SBMS Bluetooth Service destroyed")
        pollingJob?.cancel()
        serviceScope.cancel()
        super.onDestroy()
    }

    /**
     * Start monitoring Bluetooth OPP folder for incoming messages
     */
    private fun startBluetoothMonitoring() {
        pollingJob = serviceScope.launch {
            while (isActive) {
                try {
                    scanBluetoothFolder()
                    delay(POLL_INTERVAL_MS)
                } catch (e: Exception) {
                    Log.e(TAG, "Error scanning Bluetooth folder", e)
                    delay(POLL_INTERVAL_MS)
                }
            }
        }
    }

    /**
     * Scan all possible Bluetooth OPP folders for incoming messages
     */
    private suspend fun scanBluetoothFolder() {
        for (path in BLUETOOTH_OPP_PATHS) {
            val folder = File(path)
            if (!folder.exists() || !folder.isDirectory) continue

            try {
                val vCardFiles = folder.listFiles { file ->
                    file.isFile && 
                    (file.name.endsWith(".vcd") || file.name.endsWith(".vcf")) &&
                    !lastProcessedFiles.contains(file.absolutePath)
                } ?: continue

                for (file in vCardFiles) {
                    try {
                        processIncomingVCard(file)
                        lastProcessedFiles.add(file.absolutePath)
                    } catch (e: Exception) {
                        Log.e(TAG, "Error processing file: ${file.name}", e)
                    }
                }
                return // Found and processed folder, exit
            } catch (e: Exception) {
                Log.d(TAG, "Cannot access $path: ${e.message}")
            }
        }
    }

    /**
     * Process an incoming vCard file from Bluetooth OPP
     */
    private suspend fun processIncomingVCard(file: File) {
        Log.i(TAG, "Processing vCard: ${file.name}")

        try {
            val vCardContent = file.readText()
            val message = SBMSMessage.fromVCard(vCardContent)
            
            if (message == null) {
                Log.w(TAG, "Failed to parse vCard: ${file.name}")
                file.delete()
                return
            }

            // Skip status/ack messages (these are responses from phone)
            if (message.messageType != SBMSMessage.MessageType.SMS) {
                Log.d(TAG, "Skipping non-SMS message type: ${message.messageType}")
                file.delete()
                return
            }

            // Validate message
            if (!isValidMessage(message)) {
                Log.w(TAG, "Invalid message: $message")
                file.delete()
                return
            }

            Log.i(TAG, "Received SBMS message: TO=${message.to}, TEXT=${message.text.take(50)}...")

            // Send SMS
            val success = smsManager.sendSMS(message.to, message.text)
            
            // Generate response
            val status = if (success) "SENT" else "FAILED"
            val responseMessage = SBMSMessage(
                to = message.to,
                text = message.text,
                uuid = message.uuid,
                priority = message.priority,
                timestamp = System.currentTimeMillis(),
                messageType = SBMSMessage.MessageType.STATUS
            ).apply {
                // Add status field to response
            }

            Log.i(TAG, "SBMS message processed - Status: $status")

            // TODO: Push response back to E1310E via Bluetooth OPP
            // This will be implemented in Phase 3.2
            
            // Delete processed file
            file.delete()
            Log.d(TAG, "Deleted processed file: ${file.name}")

        } catch (e: Exception) {
            Log.e(TAG, "Exception processing vCard file", e)
        }
    }

    /**
     * Validate message before sending
     */
    private fun isValidMessage(message: SBMSMessage): Boolean {
        // Phone number validation (E.164 format or +[1-9]{1,14})
        if (!isValidPhoneNumber(message.to)) {
            Log.w(TAG, "Invalid phone number: ${message.to}")
            return false
        }

        // Text validation (max 160 chars for GSM-7, 70 for UCS-2)
        if (message.text.isEmpty() || message.text.length > 160) {
            Log.w(TAG, "Invalid message text length: ${message.text.length}")
            return false
        }

        // UUID validation (should be hex string)
        if (message.uuid.isEmpty() || !message.uuid.all { it in '0'..'9' || it in 'a'..'f' || it in 'A'..'F' }) {
            Log.w(TAG, "Invalid UUID format: ${message.uuid}")
            return false
        }

        return true
    }

    /**
     * Validate E.164 format phone numbers
     * Format: +[1-9]{1,14}
     */
    private fun isValidPhoneNumber(phoneNumber: String): Boolean {
        val e164Regex = Regex("^\\+[1-9]\\d{1,14}$")
        val localRegex = Regex("^0[1-9]\\d{7,9}$") // Swedish format: 0701234567
        
        return e164Regex.matches(phoneNumber) || localRegex.matches(phoneNumber)
    }
}
