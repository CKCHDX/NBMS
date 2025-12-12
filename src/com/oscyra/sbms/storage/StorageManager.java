package com.oscyra.sbms.storage;

import java.io.*;
import javax.microedition.io.*;

/**
 * Manages local file storage for messages and contacts
 */
public class StorageManager {
    private static final String BASE_PATH = "file:///";
    private static final String MSG_FOLDER = "Message/";
    private static final String SENT_FOLDER = "Message/Sent/";
    private static final String DRAFTS_FOLDER = "Message/Drafts/";

    public StorageManager() {
    }

    public void saveMessage(String filename, String content) throws IOException {
        FileConnection fc = (FileConnection) Connector.open(BASE_PATH + MSG_FOLDER + filename);
        if (!fc.exists()) {
            fc.create();
        }
        
        OutputStream os = fc.openOutputStream();
        os.write(content.getBytes("UTF-8"));
        os.close();
        fc.close();
    }

    public String readMessage(String filename) throws IOException {
        FileConnection fc = (FileConnection) Connector.open(BASE_PATH + MSG_FOLDER + filename);
        if (!fc.exists()) {
            return null;
        }
        
        InputStream is = fc.openInputStream();
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        byte[] buffer = new byte[256];
        int read;
        while ((read = is.read(buffer)) != -1) {
            baos.write(buffer, 0, read);
        }
        is.close();
        fc.close();
        
        return baos.toString();
    }

    public void moveToSent(String filename) throws IOException {
        String content = readMessage(filename);
        if (content != null) {
            FileConnection sentFc = (FileConnection) Connector.open(BASE_PATH + SENT_FOLDER + filename);
            if (!sentFc.exists()) {
                sentFc.create();
            }
            OutputStream os = sentFc.openOutputStream();
            os.write(content.getBytes("UTF-8"));
            os.close();
            sentFc.close();
            
            // Delete from inbox
            FileConnection fc = (FileConnection) Connector.open(BASE_PATH + MSG_FOLDER + filename);
            if (fc.exists()) {
                fc.delete();
            }
            fc.close();
        }
    }
}
