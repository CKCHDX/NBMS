package com.oscyra.sbms.data;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.Query;
import androidx.room.Update;

import java.util.List;

@Dao
public interface ContactDao {
    @Insert
    void insert(Contact contact);

    @Update
    void update(Contact contact);

    @Query("SELECT * FROM contacts ORDER BY displayName ASC")
    List<Contact> getAllContacts();

    @Query("SELECT * FROM contacts WHERE phoneNumber = :phoneNumber LIMIT 1")
    Contact getContactByPhone(String phoneNumber);

    @Query("SELECT * FROM contacts WHERE displayName LIKE :query ORDER BY displayName ASC")
    List<Contact> searchContacts(String query);
}
