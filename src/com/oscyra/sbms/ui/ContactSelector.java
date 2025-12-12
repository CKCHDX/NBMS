package com.oscyra.sbms.ui;

import javax.microedition.lcdui.*;
import java.util.*;

import com.oscyra.sbms.storage.Contact;
import com.oscyra.sbms.storage.ContactManager;

/**
 * Contact selection screen
 */
public class ContactSelector extends List implements CommandListener {
    private ContactManager contactManager;
    private Vector contacts;
    private CommandListener parentListener;
    private Command selectCommand;
    private Command backCommand;

    public ContactSelector(ContactManager contactManager, CommandListener parentListener) {
        super("Select Contact", List.IMPLICIT);
        this.contactManager = contactManager;
        this.parentListener = parentListener;
        this.contacts = contactManager.getStoredContacts();

        selectCommand = new Command("Select", Command.OK, 1);
        backCommand = new Command("Back", Command.BACK, 2);

        loadContacts();
        addCommand(selectCommand);
        addCommand(backCommand);
        setCommandListener(this);
    }

    private void loadContacts() {
        for (int i = 0; i < contacts.size(); i++) {
            Contact contact = (Contact) contacts.elementAt(i);
            append(contact.getDisplayName() + " (" + contact.getPhoneNumber() + ")", null);
        }
    }

    public void commandAction(Command c, Displayable d) {
        if (c == selectCommand) {
            int index = getSelectedIndex();
            if (index >= 0 && index < contacts.size()) {
                Contact selected = (Contact) contacts.elementAt(index);
                // Notify parent via custom event
                parentListener.commandAction(new Command("CONTACT_SELECTED", 0, 0), d);
            }
        } else if (c == backCommand) {
            parentListener.commandAction(backCommand, d);
        }
    }

    public Contact getSelectedContact() {
        int index = getSelectedIndex();
        if (index >= 0 && index < contacts.size()) {
            return (Contact) contacts.elementAt(index);
        }
        return null;
    }
}
