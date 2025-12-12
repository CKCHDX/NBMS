package com.oscyra.sbms.data;

import androidx.room.Database;
import androidx.room.RoomDatabase;

@Database(entities = {Contact.class, Message.class}, version = 1)
public abstract class AppDatabase extends RoomDatabase {
    public abstract ContactDao contactDao();
    public abstract MessageDao messageDao();
}
