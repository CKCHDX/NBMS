package com.ckchdx.sbms.model

import java.io.Serializable
import java.util.*

/**
 * SBMS Message Model
 * Represents a message transferred via Bluetooth OPP
 *
 * vCard Format:
 * BEGIN:VCARD
 * VERSION:2.1
 * PRODID:-//SBMS//1.0//EN
 * X-SBMS-MSG:true
 * X-SBMS-TO:+46701234567
 * X-SBMS-TEXT:Hello from E1310E
 * X-SBMS-PRIORITY:1
 * X-SBMS-TIMESTAMP:20251211T150700Z
 * X-SBMS-UUID:abc123def456
 * END:VCARD
 */
data class SBMSMessage(
    val to: String,                    // Phone number in E.164 format
    val text: String,                  // Message text (max 160 chars for SMS)
    val uuid: String,                  // Unique identifier (deterministic SHA1)
    val priority: Int = 1,             // 0=Low, 1=Normal, 2=Urgent
    val timestamp: Long = System.currentTimeMillis(),
    val messageType: MessageType = MessageType.SMS
) : Serializable {

    enum class MessageType(val value: Int) {
        SMS(1),
        STATUS(2),
        ACK(3)
    }

    /**
     * Convert SBMS message to vCard format (text-based)
     * This is the format transmitted via Bluetooth OPP
     */
    fun toVCard(): String {
        val timestamp = formatTimestamp(this.timestamp)
        return """
BEGIN:VCARD
VERSION:2.1
PRODID:-//SBMS//1.0//EN
X-SBMS-MSG:true
X-SBMS-TYPE:${messageType.value}
X-SBMS-TO:$to
X-SBMS-TEXT:${escapeVCardValue(text)}
X-SBMS-PRIORITY:$priority
X-SBMS-TIMESTAMP:$timestamp
X-SBMS-UUID:$uuid
END:VCARD
        """.trimIndent()
    }

    private fun escapeVCardValue(value: String): String {
        // Escape special characters in vCard values
        return value
            .replace("\\", "\\\\")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace(";", "\\;")
    }

    private fun formatTimestamp(timeMillis: Long): String {
        val calendar = Calendar.getInstance(TimeZone.getTimeZone("UTC"))
        calendar.timeInMillis = timeMillis
        return String.format(
            "%04d%02d%02dT%02d%02d%02dZ",
            calendar.get(Calendar.YEAR),
            calendar.get(Calendar.MONTH) + 1,
            calendar.get(Calendar.DAY_OF_MONTH),
            calendar.get(Calendar.HOUR_OF_DAY),
            calendar.get(Calendar.MINUTE),
            calendar.get(Calendar.SECOND)
        )
    }

    companion object {
        /**
         * Parse vCard-formatted message from Bluetooth OPP
         */
        fun fromVCard(vCardContent: String): SBMSMessage? {
            return try {
                val lines = vCardContent.split("\n")
                val data = mutableMapOf<String, String>()

                for (line in lines) {
                    val trimmed = line.trim()
                    if (trimmed.startsWith("X-SBMS-")) {
                        val parts = trimmed.split(":", limit = 2)
                        if (parts.size == 2) {
                            data[parts[0]] = unescapeVCardValue(parts[1])
                        }
                    }
                }

                val to = data["X-SBMS-TO"] ?: return null
                val text = data["X-SBMS-TEXT"] ?: return null
                val uuid = data["X-SBMS-UUID"] ?: return null
                val priority = data["X-SBMS-PRIORITY"]?.toIntOrNull() ?: 1
                val timestamp = data["X-SBMS-TIMESTAMP"]?.let { parseTimestamp(it) }
                    ?: System.currentTimeMillis()
                val messageType = data["X-SBMS-TYPE"]?.toIntOrNull()
                    ?.let { MessageType.values().find { mt -> mt.value == it } }
                    ?: MessageType.SMS

                SBMSMessage(
                    to = to,
                    text = text,
                    uuid = uuid,
                    priority = priority,
                    timestamp = timestamp,
                    messageType = messageType
                )
            } catch (e: Exception) {
                null
            }
        }

        private fun unescapeVCardValue(value: String): String {
            return value
                .replace("\\n", "\n")
                .replace("\\r", "\r")
                .replace("\\;", ";")
                .replace("\\\\", "\\")
        }

        private fun parseTimestamp(isoTimestamp: String): Long {
            // Parse ISO 8601 timestamp: 20251211T150700Z
            return try {
                val year = isoTimestamp.substring(0, 4).toInt()
                val month = isoTimestamp.substring(4, 6).toInt() - 1 // Calendar months are 0-indexed
                val day = isoTimestamp.substring(6, 8).toInt()
                val hour = isoTimestamp.substring(9, 11).toInt()
                val minute = isoTimestamp.substring(11, 13).toInt()
                val second = isoTimestamp.substring(13, 15).toInt()

                val calendar = Calendar.getInstance(TimeZone.getTimeZone("UTC"))
                calendar.set(year, month, day, hour, minute, second)
                calendar.timeInMillis
            } catch (e: Exception) {
                System.currentTimeMillis()
            }
        }
    }
}
