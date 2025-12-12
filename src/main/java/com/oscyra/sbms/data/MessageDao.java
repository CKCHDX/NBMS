package com.oscyra.sbms.data;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.Query;
import androidx.room.Update;

import java.util.List;

@Dao
public interface MessageDao {
    @Insert
    void insert(Message message);

    @Update
    void update(Message message);

    @Query("SELECT * FROM messages WHERE recipientPhoneNumber = :phoneNumber OR senderPhoneNumber = :phoneNumber ORDER BY timestamp DESC")
    List<Message> getMessagesWithContact(String phoneNumber);

    @Query("SELECT * FROM messages WHERE isSent = 1 ORDER BY timestamp DESC")
    List<Message> getSentMessages();

    @Query("SELECT * FROM messages WHERE isSent = 0 ORDER BY timestamp DESC")
    List<Message> getReceivedMessages();

    @Query("SELECT * FROM messages ORDER BY timestamp DESC")
    List<Message> getAllMessages();
}
