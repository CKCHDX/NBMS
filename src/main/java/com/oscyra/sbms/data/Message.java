package com.oscyra.sbms.data;

import androidx.room.Entity;
import androidx.room.PrimaryKey;

@Entity(tableName = "messages")
public class Message {
    @PrimaryKey(autoGenerate = true)
    private int id;
    private String senderPhoneNumber;
    private String recipientPhoneNumber;
    private String messageText;
    private long timestamp;
    private boolean isSent;
    private String uuid;
    private String status; // PENDING, SENT, DELIVERED, FAILED

    public Message(String senderPhoneNumber, String recipientPhoneNumber, String messageText, boolean isSent) {
        this.senderPhoneNumber = senderPhoneNumber;
        this.recipientPhoneNumber = recipientPhoneNumber;
        this.messageText = messageText;
        this.isSent = isSent;
        this.timestamp = System.currentTimeMillis();
        this.status = "PENDING";
    }

    // Getters and Setters
    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public String getSenderPhoneNumber() { return senderPhoneNumber; }
    public void setSenderPhoneNumber(String senderPhoneNumber) { this.senderPhoneNumber = senderPhoneNumber; }

    public String getRecipientPhoneNumber() { return recipientPhoneNumber; }
    public void setRecipientPhoneNumber(String recipientPhoneNumber) { this.recipientPhoneNumber = recipientPhoneNumber; }

    public String getMessageText() { return messageText; }
    public void setMessageText(String messageText) { this.messageText = messageText; }

    public long getTimestamp() { return timestamp; }
    public void setTimestamp(long timestamp) { this.timestamp = timestamp; }

    public boolean isSent() { return isSent; }
    public void setSent(boolean sent) { isSent = sent; }

    public String getUuid() { return uuid; }
    public void setUuid(String uuid) { this.uuid = uuid; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
}
