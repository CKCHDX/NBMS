package com.oscyra.sbms.android.util;

import java.security.MessageDigest;
import java.nio.charset.StandardCharsets;

/**
 * Generates deterministic UUIDs for SBMS messages.
 * Both E1310E and Android use identical logic for UUID matching.
 */
public class SbmsUuid {
    
    /**
     * Generate SBMS UUID from message components.
     * Format: First 8 characters of SHA-1 hash (uppercase hex)
     * 
     * @param phoneNumber Recipient phone number
     * @param messageText Message text content
     * @param timestampSeconds Unix timestamp in seconds
     * @return 8-character hex string UUID
     */
    public static String generate(String phoneNumber, String messageText, long timestampSeconds) {
        try {
            String combined = phoneNumber + ":" + messageText + ":" + timestampSeconds;
            MessageDigest digest = MessageDigest.getInstance("SHA-1");
            byte[] hash = digest.digest(combined.getBytes(StandardCharsets.UTF_8));
            
            // Convert first 4 bytes to 8 hex chars
            StringBuilder hexString = new StringBuilder();
            for (int i = 0; i < 4; i++) {
                String hex = Integer.toHexString(0xff & hash[i]);
                if (hex.length() == 1) hexString.append('0');
                hexString.append(hex);
            }
            return hexString.toString().toUpperCase();
        } catch (Exception e) {
            // Fallback: use system hash
            return Integer.toHexString(System.identityHashCode(phoneNumber + messageText + timestampSeconds))
                    .substring(0, Math.min(8, Integer.toHexString(System.identityHashCode(phoneNumber + messageText + timestampSeconds)).length()))
                    .toUpperCase();
        }
    }
    
    /**
     * Generate SBMS UUID with current timestamp
     */
    public static String generate(String phoneNumber, String messageText) {
        return generate(phoneNumber, messageText, System.currentTimeMillis() / 1000);
    }
}
