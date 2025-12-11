package com.oscyra.sbms.android.util;

import java.util.HashMap;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Parses SBMS vCard format messages.
 * Handles both text-based vCard 2.1 with X-SBMS extensions.
 */
public class VCardParser {
    
    private static final String TAG = "VCardParser";
    
    public static class SbmsMessage {
        public boolean isMessage;
        public String to;
        public String text;
        public String uuid;
        public long timestamp;
        public int priority;
        public String status; // For response messages
        public String delivery; // For response messages
        
        public SbmsMessage() {
            this.isMessage = false;
            this.priority = 1;
            this.timestamp = System.currentTimeMillis() / 1000;
        }
        
        @Override
        public String toString() {
            return String.format("SbmsMessage{to='%s', text='%s', uuid='%s', status='%s'}",
                    to, text, uuid, status);
        }
    }
    
    /**
     * Parse vCard text into SBMS message
     */
    public static SbmsMessage parse(String vCardText) {
        SbmsMessage msg = new SbmsMessage();
        
        if (vCardText == null || vCardText.isEmpty()) {
            return msg;
        }
        
        // Extract X-SBMS-MSG field
        String isMsgValue = extractField(vCardText, "X-SBMS-MSG");
        msg.isMessage = "true".equalsIgnoreCase(isMsgValue);
        
        // Extract recipient
        msg.to = extractField(vCardText, "X-SBMS-TO");
        
        // Extract text
        msg.text = extractField(vCardText, "X-SBMS-TEXT");
        
        // Extract UUID
        msg.uuid = extractField(vCardText, "X-SBMS-UUID");
        
        // Extract priority
        String priorityStr = extractField(vCardText, "X-SBMS-PRIORITY");
        try {
            msg.priority = Integer.parseInt(priorityStr);
        } catch (Exception e) {
            msg.priority = 1;
        }
        
        // Extract timestamp
        String timestampStr = extractField(vCardText, "X-SBMS-TIMESTAMP");
        msg.timestamp = parseTimestamp(timestampStr);
        
        // Extract status (for responses)
        msg.status = extractField(vCardText, "X-SBMS-STATUS");
        msg.delivery = extractField(vCardText, "X-SBMS-DELIVERY");
        
        return msg;
    }
    
    /**
     * Generate vCard from SBMS message
     */
    public static String toVCard(SbmsMessage msg) {
        StringBuilder sb = new StringBuilder();
        sb.append("BEGIN:VCARD\n");
        sb.append("VERSION:2.1\n");
        sb.append("PRODID:-//SBMS//1.0//EN\n");
        
        if (msg.isMessage) {
            sb.append("X-SBMS-MSG:true\n");
            sb.append(String.format("X-SBMS-TO:%s\n", escapeField(msg.to)));
            sb.append(String.format("X-SBMS-TEXT:%s\n", escapeField(msg.text)));
            sb.append(String.format("X-SBMS-PRIORITY:%d\n", msg.priority));
        } else {
            // Status response
            sb.append("X-SBMS-MSG:false\n");
            if (msg.status != null) {
                sb.append(String.format("X-SBMS-STATUS:%s\n", msg.status));
            }
            if (msg.delivery != null) {
                sb.append(String.format("X-SBMS-DELIVERY:%s\n", msg.delivery));
            }
        }
        
        // Common fields
        sb.append(String.format("X-SBMS-TIMESTAMP:%s\n", formatTimestamp(msg.timestamp)));
        sb.append(String.format("X-SBMS-UUID:%s\n", msg.uuid));
        sb.append("END:VCARD\n");
        
        return sb.toString();
    }
    
    /**
     * Extract field value from vCard
     */
    private static String extractField(String vCardText, String fieldName) {
        Pattern pattern = Pattern.compile(fieldName + ":([^\n\r]+)");
        Matcher matcher = pattern.matcher(vCardText);
        if (matcher.find()) {
            return matcher.group(1).trim();
        }
        return "";
    }
    
    /**
     * Escape field value for vCard format
     */
    private static String escapeField(String value) {
        if (value == null) return "";
        return value.replace("\n", "\\n").replace("\r", "\\r");
    }
    
    /**
     * Parse ISO 8601 timestamp to Unix seconds
     */
    private static long parseTimestamp(String isoTimestamp) {
        try {
            if (isoTimestamp == null || isoTimestamp.isEmpty()) {
                return System.currentTimeMillis() / 1000;
            }
            
            // Format: 20251211T150700Z
            String clean = isoTimestamp.replace("T", "").replace("Z", "");
            if (clean.length() < 14) {
                return System.currentTimeMillis() / 1000;
            }
            
            int year = Integer.parseInt(clean.substring(0, 4));
            int month = Integer.parseInt(clean.substring(4, 6));
            int day = Integer.parseInt(clean.substring(6, 8));
            int hour = Integer.parseInt(clean.substring(8, 10));
            int minute = Integer.parseInt(clean.substring(10, 12));
            int second = Integer.parseInt(clean.substring(12, 14));
            
            // Simple approximation (use Java Calendar for production)
            long daysPerYear = 365L;
            long secondsPerDay = 86400L;
            long secondsSince1970 = ((year - 1970) * daysPerYear + (month - 1) * 30 + (day - 1)) * secondsPerDay
                    + hour * 3600 + minute * 60 + second;
            
            return secondsSince1970;
        } catch (Exception e) {
            return System.currentTimeMillis() / 1000;
        }
    }
    
    /**
     * Format Unix seconds to ISO 8601
     */
    private static String formatTimestamp(long secondsSince1970) {
        java.util.Calendar cal = java.util.Calendar.getInstance(java.util.TimeZone.getTimeZone("UTC"));
        cal.setTimeInMillis(secondsSince1970 * 1000);
        return String.format("%04d%02d%02dT%02d%02d%02dZ",
                cal.get(java.util.Calendar.YEAR),
                cal.get(java.util.Calendar.MONTH) + 1,
                cal.get(java.util.Calendar.DAY_OF_MONTH),
                cal.get(java.util.Calendar.HOUR_OF_DAY),
                cal.get(java.util.Calendar.MINUTE),
                cal.get(java.util.Calendar.SECOND));
    }
}
