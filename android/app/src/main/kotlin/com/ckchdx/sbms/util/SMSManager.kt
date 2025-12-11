package com.ckchdx.sbms.util

import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import android.telephony.SmsManager
import android.util.Log

/**
 * SMS Manager Utility
 * 
 * Handles sending SMS messages via Android's native SmsManager API
 * Also captures delivery receipts and SMS sent callbacks
 */
class SMSManager(private val context: Context) {

    companion object {
        private const val TAG = "SMSManager"
        const val ACTION_SMS_SENT = "com.ckchdx.sbms.SMS_SENT"
        const val ACTION_SMS_DELIVERED = "com.ckchdx.sbms.SMS_DELIVERED"
    }

    /**
     * Send SMS message
     * 
     * @param phoneNumber Recipient phone number (E.164 format or local format)
     * @param messageText Message content (max 160 chars recommended)
     * @return true if SMS was queued successfully, false otherwise
     */
    fun sendSMS(phoneNumber: String, messageText: String): Boolean {
        return try {
            val smsManager = context.getSystemService(Context.TELEPHONY_SERVICE) as SmsManager
            
            // Normalize phone number
            val normalizedNumber = normalizePhoneNumber(phoneNumber)
            
            Log.i(TAG, "Sending SMS to: $normalizedNumber, Text length: ${messageText.length}")
            
            // For long messages, automatically split into multiple SMS
            val parts = smsManager.divideMessage(messageText)
            
            if (parts.size == 1) {
                // Single SMS
                sendSingleSMS(smsManager, normalizedNumber, messageText)
            } else {
                // Multi-part SMS
                sendMultiPartSMS(smsManager, normalizedNumber, parts)
            }
            
            true
        } catch (e: Exception) {
            Log.e(TAG, "Error sending SMS", e)
            false
        }
    }

    /**
     * Send a single SMS message
     */
    private fun sendSingleSMS(
        smsManager: SmsManager,
        phoneNumber: String,
        message: String
    ) {
        val sentIntent = createSentIntent()
        val deliveryIntent = createDeliveryIntent()
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            // Android 10+ requires subscription ID
            try {
                smsManager.sendTextMessage(
                    phoneNumber,
                    null,
                    message,
                    sentIntent,
                    deliveryIntent
                )
            } catch (e: Exception) {
                Log.e(TAG, "Error with Q+ SMS API", e)
                // Fallback
                smsManager.sendTextMessage(phoneNumber, null, message, sentIntent, deliveryIntent)
            }
        } else {
            smsManager.sendTextMessage(phoneNumber, null, message, sentIntent, deliveryIntent)
        }
        
        Log.d(TAG, "Single SMS queued to: $phoneNumber")
    }

    /**
     * Send multi-part SMS message (split across multiple messages)
     */
    private fun sendMultiPartSMS(
        smsManager: SmsManager,
        phoneNumber: String,
        parts: List<String>
    ) {
        val sentIntents = mutableListOf<PendingIntent>()
        val deliveryIntents = mutableListOf<PendingIntent>()
        
        for (i in parts.indices) {
            sentIntents.add(createSentIntent(i, parts.size))
            deliveryIntents.add(createDeliveryIntent(i, parts.size))
        }
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP_MR1) {
            smsManager.sendMultipartTextMessage(
                phoneNumber,
                null,
                parts,
                sentIntents,
                deliveryIntents
            )
        }
        
        Log.d(TAG, "Multi-part SMS (${parts.size} parts) queued to: $phoneNumber")
    }

    /**
     * Create PendingIntent for SMS sent callback
     */
    private fun createSentIntent(partNumber: Int = 0, totalParts: Int = 1): PendingIntent {
        val intent = Intent(ACTION_SMS_SENT).apply {
            setPackage(context.packageName)
            putExtra("phoneNumber", "")
            putExtra("partNumber", partNumber)
            putExtra("totalParts", totalParts)
        }
        
        val flags = PendingIntent.FLAG_UPDATE_CURRENT or 
            (if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) PendingIntent.FLAG_IMMUTABLE else 0)
        
        return PendingIntent.getBroadcast(
            context,
            ACTION_SMS_SENT.hashCode() + partNumber,
            intent,
            flags
        )
    }

    /**
     * Create PendingIntent for SMS delivery callback
     */
    private fun createDeliveryIntent(partNumber: Int = 0, totalParts: Int = 1): PendingIntent {
        val intent = Intent(ACTION_SMS_DELIVERED).apply {
            setPackage(context.packageName)
            putExtra("phoneNumber", "")
            putExtra("partNumber", partNumber)
            putExtra("totalParts", totalParts)
        }
        
        val flags = PendingIntent.FLAG_UPDATE_CURRENT or 
            (if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) PendingIntent.FLAG_IMMUTABLE else 0)
        
        return PendingIntent.getBroadcast(
            context,
            ACTION_SMS_DELIVERED.hashCode() + partNumber,
            intent,
            flags
        )
    }

    /**
     * Normalize phone number to E.164 format
     * Handles both international (+46...) and local (070...) formats
     */
    private fun normalizePhoneNumber(phoneNumber: String): String {
        return when {
            phoneNumber.startsWith("+") -> {
                // Already in E.164 format
                phoneNumber
            }
            phoneNumber.startsWith("00") -> {
                // Convert 00 to +
                "+" + phoneNumber.substring(2)
            }
            phoneNumber.startsWith("0") -> {
                // Swedish local format (0701234567 -> +46701234567)
                // Assumes Swedish numbers starting with 0
                "+46" + phoneNumber.substring(1)
            }
            else -> {
                // Assume it's already formatted or international without +
                "+$phoneNumber"
            }
        }
    }
}
