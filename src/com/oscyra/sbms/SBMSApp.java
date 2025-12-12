package com.oscyra.sbms;

import javax.microedition.lcdui.*;
import javax.microedition.midlet.MIDlet;
import javax.microedition.midlet.MIDletStateChangeException;

/**
 * Samsung Bluetooth Message Service - E1310E Edition
 * Main MIDlet entry point for J2ME application
 */
public class SBMSApp extends MIDlet {
    private MainScreen mainScreen;
    private Display display;

    protected void startApp() throws MIDletStateChangeException {
        display = Display.getDisplay(this);
        if (mainScreen == null) {
            mainScreen = new MainScreen(this);
        }
        display.setCurrent(mainScreen);
    }

    protected void pauseApp() {
    }

    protected void destroyApp(boolean unconditional) throws MIDletStateChangeException {
        if (mainScreen != null) {
            mainScreen.cleanup();
        }
    }

    public void exit() {
        try {
            destroyApp(true);
        } catch (MIDletStateChangeException e) {
            e.printStackTrace();
        }
        notifyDestroyed();
    }
}
