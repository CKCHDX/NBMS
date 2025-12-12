package com.oscyra.sbms.storage;

import java.util.*;

/**
 * Manages contact synchronization from paired phone
 */
public class ContactManager {
    private Vector storedContacts = new Vector();

    public ContactManager() {
        // Load stored contacts from persistent storage
        loadStoredContacts();
    }

    private void loadStoredContacts() {
        // In production, load from device phonebook or PBAP (Phone Book Access Profile)
        // For now, use a sample list
        storedContacts.addElement(new Contact("Mom", "+46701234567"));
        storedContacts.addElement(new Contact("Dad", "+46702345678"));
        storedContacts.addElement(new Contact("Sister", "+46703456789"));
        storedContacts.addElement(new Contact("Work", "+46704567890"));
    }

    public Vector getStoredContacts() {
        return new Vector(storedContacts);
    }

    public Contact getContactByPhone(String phoneNumber) {
        for (int i = 0; i < storedContacts.size(); i++) {
            Contact c = (Contact) storedContacts.elementAt(i);
            if (c.getPhoneNumber().equals(phoneNumber)) {
                return c;
            }
        }
        return null;
    }

    public void addContact(Contact contact) {
        storedContacts.addElement(contact);
    }

    public void updateContact(Contact contact) {
        for (int i = 0; i < storedContacts.size(); i++) {
            Contact c = (Contact) storedContacts.elementAt(i);
            if (c.getPhoneNumber().equals(contact.getPhoneNumber())) {
                storedContacts.setElementAt(contact, i);
                return;
            }
        }
    }
}
