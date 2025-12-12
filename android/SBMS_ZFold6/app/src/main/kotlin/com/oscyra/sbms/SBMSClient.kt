package com.oscyra.sbms

import android.util.Log
import com.google.gson.Gson
import com.google.gson.JsonObject
import kotlinx.coroutines.*
import java.io.*
import java.net.Socket
import java.util.concurrent.atomic.AtomicBoolean

/**
 * SBMS Client for Android Z Fold 6
 *
 * Connects to Windows SBMS Host via TCP socket
 * Manages contacts, messages, and device communication
 *
 * Author: Alex Jonsson
 * Date: December 2025
 */

data class Contact(
    val name: String,
    val phone: String
)

data class SBMSMessage(
    val id: String,
    val to: String,
    val text: String,
    val status: String = "pending"
)

sealed class SBMSEvent {
    data class Connected(val message: String) : SBMSEvent()
    data class Disconnected(val reason: String) : SBMSEvent()
    data class Error(val error: String) : SBMSEvent()
    data class MessageReceived(val message: SBMSMessage) : SBMSEvent()
    data class ContactsReceived(val contacts: List<Contact>) : SBMSEvent()
    data class StatusUpdate(val status: String) : SBMSEvent()
}

class SBMSClient(
    private val hostAddress: String = "192.168.1.100",  // Windows host IP (change for your network)
    private val hostPort: Int = 5555,  // Bluetooth fallback port
    private val deviceName: String = "Z Fold 6"
) {
    companion object {
        private const val TAG = "SBMSClient"
        private const val SOCKET_TIMEOUT = 5000  // ms
        private const val CONNECTION_RETRY_DELAY = 3000L  // ms
        private const val MAX_RETRY_ATTEMPTS = 5
    }
    
    private var socket: Socket? = null
    private var inputStream: BufferedReader? = null
    private var outputStream: PrintWriter? = null
    private val isConnected = AtomicBoolean(false)
    private val gson = Gson()
    
    // For coroutine management
    private var connectionJob: Job? = null
    private val scope = CoroutineScope(Dispatchers.IO + Job())
    
    // Event callback
    private var onEvent: ((SBMSEvent) -> Unit)? = null
    
    fun setEventListener(listener: (SBMSEvent) -> Unit) {
        this.onEvent = listener
    }
    
    /**
     * Connect to Windows SBMS Host asynchronously
     */
    fun connect() {
        connectionJob?.cancel()
        connectionJob = scope.launch {
            var attempts = 0
            while (attempts < MAX_RETRY_ATTEMPTS && isConnected.get().not()) {
                try {
                    connectToHost()
                    if (isConnected.get()) {
                        emitEvent(SBMSEvent.Connected("Connected to SBMS host"))
                        identify()
                        // Start listening for messages
                        listenForMessages()
                    }
                    break
                } catch (e: Exception) {
                    attempts++
                    Log.w(TAG, "Connection attempt $attempts failed: ${e.message}")
                    emitEvent(SBMSEvent.Error("Connection failed (attempt $attempts/$MAX_RETRY_ATTEMPTS): ${e.message}"))
                    
                    if (attempts < MAX_RETRY_ATTEMPTS) {
                        delay(CONNECTION_RETRY_DELAY)
                    }
                }
            }
            
            if (!isConnected.get()) {
                emitEvent(SBMSEvent.Error("Failed to connect after $MAX_RETRY_ATTEMPTS attempts"))
            }
        }
    }
    
    /**
     * Connect to host (blocking operation)
     */
    private fun connectToHost() {
        try {
            Log.d(TAG, "Connecting to $hostAddress:$hostPort")
            
            socket = Socket(hostAddress, hostPort).apply {
                soTimeout = SOCKET_TIMEOUT
            }
            
            inputStream = BufferedReader(InputStreamReader(socket!!.inputStream))
            outputStream = PrintWriter(OutputStreamWriter(socket!!.outputStream), true)
            
            isConnected.set(true)
            Log.i(TAG, "Connected to host")
        } catch (e: Exception) {
            isConnected.set(false)
            throw e
        }
    }
    
    /**
     * Identify device to host
     */
    private suspend fun identify() {
        val message = JsonObject().apply {
            addProperty("type", "identify")
            addProperty("device", deviceName)
        }
        sendMessage(message)
    }
    
    /**
     * Get contacts from host
     */
    suspend fun getContacts(): List<Contact> {
        val message = JsonObject().apply {
            addProperty("type", "get_contacts")
        }
        
        return try {
            val response = sendMessageAndWaitResponse(message)
            if (response?.has("data") == true) {
                val contactsData = response.getAsJsonObject("data")
                val contacts = mutableListOf<Contact>()
                
                for ((phone, contactInfo) in contactsData.entrySet()) {
                    val obj = contactInfo.asJsonObject
                    contacts.add(Contact(
                        name = obj.get("name").asString,
                        phone = phone
                    ))
                }
                
                emitEvent(SBMSEvent.ContactsReceived(contacts))
                contacts
            } else {
                emptyList()
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error getting contacts", e)
            emitEvent(SBMSEvent.Error("Failed to get contacts: ${e.message}"))
            emptyList()
        }
    }
    
    /**
     * Sync contacts to host
     */
    suspend fun syncContacts(contacts: List<Contact>): Boolean {
        val message = JsonObject().apply {
            addProperty("type", "sync_contacts")
            add("contacts", gson.toJsonTree(contacts))
        }
        
        return try {
            val response = sendMessageAndWaitResponse(message)
            val success = response?.get("status")?.asString == "synced"
            if (success) {
                emitEvent(SBMSEvent.StatusUpdate("Synced ${contacts.size} contacts"))
            }
            success
        } catch (e: Exception) {
            Log.e(TAG, "Error syncing contacts", e)
            emitEvent(SBMSEvent.Error("Failed to sync contacts: ${e.message}"))
            false
        }
    }
    
    /**
     * Send SMS message through host
     */
    suspend fun sendSMS(to: String, text: String): String? {
        val msgId = "msg_${System.currentTimeMillis()}"
        val message = JsonObject().apply {
            addProperty("type", "send_message")
            addProperty("id", msgId)
            addProperty("to", to)
            addProperty("text", text)
        }
        
        return try {
            val response = sendMessageAndWaitResponse(message)
            val success = response?.get("status")?.asString == "queued"
            if (success) {
                emitEvent(SBMSEvent.StatusUpdate("Message queued to $to"))
                msgId
            } else {
                emitEvent(SBMSEvent.Error("Failed to queue message"))
                null
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error sending SMS", e)
            emitEvent(SBMSEvent.Error("Failed to send SMS: ${e.message}"))
            null
        }
    }
    
    /**
     * Report message delivery status
     */
    suspend fun reportSMSStatus(msgId: String, status: String): Boolean {
        val message = JsonObject().apply {
            addProperty("type", "sms_status")
            addProperty("id", msgId)
            addProperty("status", status)
        }
        
        return try {
            val response = sendMessageAndWaitResponse(message)
            response?.get("status")?.asString == "received"
        } catch (e: Exception) {
            Log.e(TAG, "Error reporting SMS status", e)
            false
        }
    }
    
    /**
     * Ping host
     */
    suspend fun ping(): Boolean {
        val message = JsonObject().apply {
            addProperty("type", "ping")
        }
        
        return try {
            val response = sendMessageAndWaitResponse(message)
            response?.get("type")?.asString == "pong"
        } catch (e: Exception) {
            Log.e(TAG, "Ping failed", e)
            false
        }
    }
    
    /**
     * Send JSON message to host
     */
    private fun sendMessage(message: JsonObject) {
        if (!isConnected.get() || outputStream == null) {
            throw IllegalStateException("Not connected to host")
        }
        
        val json = gson.toJson(message)
        Log.d(TAG, "Sending: $json")
        outputStream?.println(json)
    }
    
    /**
     * Send message and wait for response
     */
    private suspend fun sendMessageAndWaitResponse(message: JsonObject, timeoutMs: Long = 5000): JsonObject? {
        return withTimeoutOrNull(timeoutMs) {
            sendMessage(message)
            inputStream?.readLine()?.let {
                Log.d(TAG, "Received: $it")
                gson.fromJson(it, JsonObject::class.java)
            }
        }
    }
    
    /**
     * Listen for incoming messages from host
     */
    private suspend fun listenForMessages() {
        withContext(Dispatchers.IO) {
            try {
                while (isConnected.get()) {
                    val line = inputStream?.readLine() ?: break
                    Log.d(TAG, "Received message: $line")
                    
                    try {
                        val json = gson.fromJson(line, JsonObject::class.java)
                        // Handle different message types here
                    } catch (e: Exception) {
                        Log.e(TAG, "Error parsing message", e)
                    }
                }
            } catch (e: Exception) {
                if (isConnected.get()) {
                    Log.e(TAG, "Error listening for messages", e)
                    disconnect()
                    emitEvent(SBMSEvent.Disconnected("Connection lost: ${e.message}"))
                }
            }
        }
    }
    
    /**
     * Disconnect from host
     */
    fun disconnect() {
        connectionJob?.cancel()
        isConnected.set(false)
        
        try {
            outputStream?.close()
            inputStream?.close()
            socket?.close()
            Log.i(TAG, "Disconnected from host")
        } catch (e: Exception) {
            Log.e(TAG, "Error during disconnect", e)
        }
    }
    
    /**
     * Check connection status
     */
    fun isConnectedToHost(): Boolean = isConnected.get()
    
    /**
     * Emit event to listener
     */
    private fun emitEvent(event: SBMSEvent) {
        Log.d(TAG, "Event: $event")
        onEvent?.invoke(event)
    }
    
    /**
     * Cleanup on destroy
     */
    fun destroy() {
        disconnect()
        scope.cancel()
    }
}
