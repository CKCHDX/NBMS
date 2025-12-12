package com.oscyra.sbms;

import javax.microedition.lcdui.*;
import java.util.*;

import com.oscyra.sbms.bluetooth.*;
import com.oscyra.sbms.ui.*;
import com.oscyra.sbms.storage.*;

/**
 * Main UI Screen for E1310E - Message Composer
 */
public class MainScreen extends Form implements CommandListener {
    private SBMSApp midlet;
    private BluetoothHandler btHandler;
    private StorageManager storageManager;
    private ContactManager contactManager;
    private MessageComposer messageComposer;
    private Screen currentScreen;
    
    // UI Components
    private StringItem statusItem;
    private StringItem selectedContactItem;
    private TextField messageField;
    private TextField contactSearchField;
    private ChoiceGroup contactsList;
    
    // Commands
    private Command selectContactCommand;
    private Command sendMessageCommand;
    private Command exitCommand;
    private Command backCommand;
    
    private Vector contacts = new Vector();
    private Contact selectedContact = null;

    public MainScreen(SBMSApp midlet) {
        super("SBMS - E1310E");
        this.midlet = midlet;
        
        // Initialize managers
        this.btHandler = new BluetoothHandler();
        this.storageManager = new StorageManager();
        this.contactManager = new ContactManager();
        this.messageComposer = new MessageComposer();
        
        // Initialize UI
        initializeUI();
        loadContacts();
    }

    private void initializeUI() {
        // Status Item
        statusItem = new StringItem("Status: ", "Ready");
        append(statusItem);
        
        append(new StringItem("", "------- Compose Message -------"));
        
        // Contact Search
        contactSearchField = new TextField("Find Contact: ", "", 30, TextField.ANY);
        append(contactSearchField);
        
        // Contacts List
        contactsList = new ChoiceGroup("Contacts:", ChoiceGroup.EXCLUSIVE);
        append(contactsList);
        
        // Selected Contact Display
        selectedContactItem = new StringItem("To: ", "(none selected)");
        append(selectedContactItem);
        
        // Message Input
        append(new StringItem("", "Message (max 160 chars):"));
        messageField = new TextField("", "", 160, TextField.ANY);
        append(messageField);
        
        // Commands
        selectContactCommand = new Command("Select", Command.ITEM, 1);
        sendMessageCommand = new Command("Send", Command.OK, 2);
        backCommand = new Command("Back", Command.BACK, 3);
        exitCommand = new Command("Exit", Command.EXIT, 4);
        
        addCommand(selectContactCommand);
        addCommand(sendMessageCommand);
        addCommand(exitCommand);
        
        setCommandListener(this);
    }

    private void loadContacts() {
        // Load from phone's contact list (via Bluetooth)
        // For now, use stored contacts from previous sessions
        contacts = contactManager.getStoredContacts();
        
        contactsList.deleteAll();
        for (int i = 0; i < contacts.size(); i++) {
            Contact contact = (Contact) contacts.elementAt(i);
            contactsList.append(contact.getDisplayName() + " (" + contact.getPhoneNumber() + ")", null);
        }
    }

    private void filterContacts(String query) {
        contactsList.deleteAll();
        
        if (query.length() == 0) {
            loadContacts();
            return;
        }
        
        String lowerQuery = query.toLowerCase();
        for (int i = 0; i < contacts.size(); i++) {
            Contact contact = (Contact) contacts.elementAt(i);
            if (contact.getDisplayName().toLowerCase().indexOf(lowerQuery) >= 0 ||
                contact.getPhoneNumber().indexOf(query) >= 0) {
                contactsList.append(
                    contact.getDisplayName() + " (" + contact.getPhoneNumber() + ")",
                    null
                );
            }
        }
    }

    private void selectContact() {
        int selectedIndex = contactsList.getSelectedIndex();
        if (selectedIndex < 0 || selectedIndex >= contacts.size()) {
            Alert alert = new Alert("Error", "Please select a contact", null, AlertType.ERROR);
            alert.setTimeout(Alert.FOREVER);
            Display.getDisplay(midlet).setCurrent(alert, this);
            return;
        }
        
        selectedContact = (Contact) contacts.elementAt(selectedIndex);
        selectedContactItem.setText(selectedContact.getDisplayName() + " (" + selectedContact.getPhoneNumber() + ")");
    }

    private void sendMessage() {
        if (selectedContact == null) {
            showAlert("Error", "Please select a contact first", AlertType.ERROR);
            return;
        }
        
        String messageText = messageField.getString().trim();
        if (messageText.length() == 0) {
            showAlert("Error", "Message cannot be empty", AlertType.ERROR);
            return;
        }
        
        if (messageText.length() > 160) {
            showAlert("Error", "Message exceeds 160 characters", AlertType.ERROR);
            return;
        }
        
        // Create vCard message
        String vCardMessage = messageComposer.createMessage(
            selectedContact.getPhoneNumber(),
            messageText,
            generateUUID()
        );
        
        // Send via Bluetooth
        statusItem.setText("Sending...");
        btHandler.sendMessage(vCardMessage, new BluetoothHandler.SendCallback() {
            public void onResult(boolean success) {
                if (success) {
                    showAlert("Success", "Message sent to " + selectedContact.getDisplayName(), AlertType.INFO);
                    messageField.setString("");
                    selectedContact = null;
                    selectedContactItem.setText("(none selected)");
                    statusItem.setText("Ready");
                } else {
                    showAlert("Error", "Failed to send message", AlertType.ERROR);
                    statusItem.setText("Error");
                }
            }
        });
    }

    private void showAlert(String title, String message, AlertType type) {
        Alert alert = new Alert(title, message, null, type);
        alert.setTimeout(Alert.FOREVER);
        Display.getDisplay(midlet).setCurrent(alert, this);
    }

    private String generateUUID() {
        long time = System.currentTimeMillis();
        return String.valueOf(Math.abs((time * 31) ^ ("SBMS".hashCode()))).substring(0, 8);
    }

    public void commandAction(Command c, Displayable d) {
        if (c == sendMessageCommand) {
            sendMessage();
        } else if (c == selectContactCommand) {
            selectContact();
        } else if (c == exitCommand) {
            midlet.exit();
        } else if (c == backCommand) {
            Display.getDisplay(midlet).setCurrent(this);
        }
    }

    public void cleanup() {
        if (btHandler != null) {
            btHandler.disconnect();
        }
    }
}
