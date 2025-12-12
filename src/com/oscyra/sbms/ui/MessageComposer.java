package com.oscyra.sbms.ui;

import java.util.*;

/**
 * Composes vCard-formatted SBMS messages for Bluetooth transmission
 */
public class MessageComposer {

    /**
     * Create a vCard message for transmission via Bluetooth OPP
     */
    public String createMessage(String recipientPhone, String messageText, String uuid) {
        StringBuffer vcard = new StringBuffer();
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
    public String createStatusResponse(String status, String uuid) {
        StringBuffer vcard = new StringBuffer();
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
    public ParsedMessage parseMessage(String vCardData) {
        try {
            if (vCardData.indexOf("X-SBMS-MSG:true") < 0) {
                return null; // Not an SBMS message
            }

            String senderPhone = extractField(vCardData, "X-SBMS-FROM");
            String recipientPhone = extractField(vCardData, "X-SBMS-TO");
            String messageText = extractField(vCardData, "X-SBMS-TEXT");
            String uuid = extractField(vCardData, "X-SBMS-UUID");

            if (messageText == null || messageText.length() == 0) {
                return null;
            }

            return new ParsedMessage(senderPhone, recipientPhone, messageText, uuid);

        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    /**
     * Extract a specific field value from vCard data
     */
    private String extractField(String vCardData, String fieldName) {
        try {
            int startIndex = vCardData.indexOf(fieldName + ":");
            if (startIndex < 0) {
                return null;
            }
            startIndex += fieldName.length() + 1;
            int endIndex = vCardData.indexOf("\r\n", startIndex);
            if (endIndex < 0) {
                endIndex = vCardData.indexOf("\n", startIndex);
            }
            if (endIndex < 0) {
                endIndex = vCardData.length();
            }
            return vCardData.substring(startIndex, endIndex).trim();
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    /**
     * Sanitize message text for vCard compatibility
     */
    private String sanitizeText(String text) {
        return text
                .replace("\r", "")
                .replace("\n", " ")
                .replace(":", "")
                .trim();
    }

    /**
     * Get current timestamp in ISO 8601 format
     */
    private String getCurrentTimestamp() {
        Date now = new Date();
        Calendar cal = Calendar.getInstance();
        cal.setTime(now);
        
        int year = cal.get(Calendar.YEAR);
        int month = cal.get(Calendar.MONTH) + 1;
        int day = cal.get(Calendar.DAY_OF_MONTH);
        int hour = cal.get(Calendar.HOUR_OF_DAY);
        int minute = cal.get(Calendar.MINUTE);
        int second = cal.get(Calendar.SECOND);
        
        StringBuffer sb = new StringBuffer();
        sb.append(padZero(year, 4));
        sb.append(padZero(month, 2));
        sb.append(padZero(day, 2));
        sb.append("T");
        sb.append(padZero(hour, 2));
        sb.append(padZero(minute, 2));
        sb.append(padZero(second, 2));
        sb.append("Z");
        
        return sb.toString();
    }

    private String padZero(int value, int length) {
        String str = String.valueOf(value);
        while (str.length() < length) {
            str = "0" + str;
        }
        return str;
    }

    /**
     * Inner class for parsed message data
     */
    public static class ParsedMessage {
        public String senderPhone;
        public String recipientPhone;
        public String messageText;
        public String uuid;

        public ParsedMessage(String senderPhone, String recipientPhone, String messageText, String uuid) {
            this.senderPhone = senderPhone;
            this.recipientPhone = recipientPhone;
            this.messageText = messageText;
            this.uuid = uuid;
        }
    }
}
