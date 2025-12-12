package com.oscyra.sbms.utils;

import android.util.Log;

import com.oscyra.sbms.data.Message;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.UUID;

public class SBMSMessageFormatter {
    private static final String TAG = "SBMS_MessageFormatter";

    /**
     * Create a vCard message for transmission via Bluetooth OPP
     */
    public static String createVCardMessage(String recipientPhone, String messageText, String uuid) {
        StringBuilder vcard = new StringBuilder();
        vcard.append("BEGIN:VCARD\r\n");
        vcard.append("VERSION:2.1\r\n");
        vcard.append("PRODID:-//SBMS//1.0//EN\r\n");
        vcard.append("X-SBMS-MSG:true\r\n");
        vcard.append("X-SBMS-TO:").append(recipientPhone).append("\r\n");
        vcard.append("X-SBMS-TEXT:").append(sanitizeText(messageText)).append("\r\n");
        vcard.append("X-SBMS-PRIORITY:1\r\n");
        vcard.append("X-SBMS-TIMESTAMP:").append(getCurrentTimestamp()).append("\r\n");
        vcard.append("X-SBMS-UUID:").append(uuid).append("\r\n");
        vcard.append("END:VCARD\r\n");
        return vcard.toString();
    }

    /**
     * Create a response vCard for delivery status
     */
    public static String createStatusResponse(String recipientPhone, String status, String uuid) {
        StringBuilder vcard = new StringBuilder();
        vcard.append("BEGIN:VCARD\r\n");
        vcard.append("VERSION:2.1\r\n");
        vcard.append("PRODID:-//SBMS//1.0//EN\r\n");
        vcard.append("X-SBMS-RESPONSE:true\r\n");
        vcard.append("X-SBMS-STATUS:").append(status).append("\r\n");
        vcard.append("X-SBMS-TIMESTAMP:").append(getCurrentTimestamp()).append("\r\n");
        vcard.append("X-SBMS-UUID:").append(uuid).append("\r\n");
        vcard.append("END:VCARD\r\n");
        return vcard.toString();
    }

    /**
     * Parse incoming vCard message
     */
    public static Message parseVCardMessage(String vCardData) {
        try {
            if (!vCardData.contains("X-SBMS-MSG:true")) {
                return null; // Not an SBMS message
            }

            String senderPhone = extractField(vCardData, "X-SBMS-FROM");
            String recipientPhone = extractField(vCardData, "X-SBMS-TO");
            String messageText = extractField(vCardData, "X-SBMS-TEXT");
            String uuid = extractField(vCardData, "X-SBMS-UUID");

            if (messageText == null || messageText.isEmpty()) {
                return null;
            }

            // If FROM is missing, this is a received message
            if (senderPhone == null || senderPhone.isEmpty()) {
                senderPhone = recipientPhone; // Infer sender as current message recipient
                recipientPhone = "+"; // Placeholder
            }

            Message message = new Message(
                    senderPhone,
                    recipientPhone,
                    messageText,
                    false // Received message
            );
            message.setUuid(uuid);
            message.setStatus("RECEIVED");
            return message;

        } catch (Exception e) {
            Log.e(TAG, "Error parsing vCard", e);
            return null;
        }
    }

    /**
     * Extract a specific field value from vCard data
     */
    private static String extractField(String vCardData, String fieldName) {
        try {
            int startIndex = vCardData.indexOf(fieldName + ":");
            if (startIndex == -1) {
                return null;
            }
            startIndex += fieldName.length() + 1;
            int endIndex = vCardData.indexOf("\r\n", startIndex);
            if (endIndex == -1) {
                endIndex = vCardData.indexOf("\n", startIndex);
            }
            if (endIndex == -1) {
                endIndex = vCardData.length();
            }
            return vCardData.substring(startIndex, endIndex).trim();
        } catch (Exception e) {
            Log.e(TAG, "Error extracting field: " + fieldName, e);
            return null;
        }
    }

    /**
     * Sanitize message text to remove problematic characters
     */
    private static String sanitizeText(String text) {
        return text
                .replace("\r", "")
                .replace("\n", " ")
                .replace(":", "")
                .trim();
    }

    /**
     * Get current timestamp in ISO 8601 format
     */
    private static String getCurrentTimestamp() {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd'T'HHmmss'Z'", Locale.US);
        return sdf.format(new Date());
    }
}
