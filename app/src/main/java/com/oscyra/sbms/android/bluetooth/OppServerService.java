package com.oscyra.sbms.android.bluetooth;

import android.app.Service;
import android.content.Intent;
import android.os.Environment;
import android.os.IBinder;
import android.util.Log;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Timer;
import java.util.TimerTask;

import com.oscyra.sbms.android.util.VCardParser;

/**
 * Service that monitors Bluetooth OPP folder for incoming messages from E1310E.
 * When a message file is detected, it parses the vCard and relays via SMS.
 */
public class OppServerService extends Service {
    
    private static final String TAG = "SBMS.OppServerService";
    private static final long POLL_INTERVAL_MS = 2000; // Poll every 2 seconds
    
    private Timer monitorTimer;
    private File bluetoothFolder;
    
    @Override
    public void onCreate() {
        super.onCreate();
        Log.d(TAG, "OppServerService created");
        
        // Initialize Bluetooth folder path (Android 10+)
        bluetoothFolder = new File(
                Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),
                "Bluetooth"
        );
        
        if (!bluetoothFolder.exists()) {
            bluetoothFolder.mkdirs();
        }
        
        Log.d(TAG, "Monitoring folder: " + bluetoothFolder.getAbsolutePath());
    }
    
    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Log.d(TAG, "OppServerService started");
        startMonitoring();
        return START_STICKY;
    }
    
    @Override
    public IBinder onBind(Intent intent) {
        return null; // Not a bound service
    }
    
    @Override
    public void onDestroy() {
        super.onDestroy();
        stopMonitoring();
        Log.d(TAG, "OppServerService destroyed");
    }
    
    /**
     * Start monitoring Bluetooth folder for incoming OPP messages
     */
    private void startMonitoring() {
        if (monitorTimer != null) {
            return; // Already running
        }
        
        monitorTimer = new Timer();
        monitorTimer.scheduleAtFixedRate(new TimerTask() {
            @Override
            public void run() {
                scanBluetoothFolder();
            }
        }, 0, POLL_INTERVAL_MS);
        
        Log.d(TAG, "Monitoring started");
    }
    
    /**
     * Stop monitoring
     */
    private void stopMonitoring() {
        if (monitorTimer != null) {
            monitorTimer.cancel();
            monitorTimer = null;
        }
        Log.d(TAG, "Monitoring stopped");
    }
    
    /**
     * Scan Bluetooth folder for new message files
     */
    private void scanBluetoothFolder() {
        try {
            if (!bluetoothFolder.exists()) {
                return;
            }
            
            File[] files = bluetoothFolder.listFiles((dir, name) ->
                    name.startsWith("message_") && (name.endsWith(".vcd") || name.endsWith(".vcf"))
            );
            
            if (files != null) {
                for (File file : files) {
                    processMessageFile(file);
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "Error scanning Bluetooth folder", e);
        }
    }
    
    /**
     * Process a single message file
     */
    private void processMessageFile(File file) {
        try {
            Log.d(TAG, "Processing message file: " + file.getName());
            
            // Read file content
            String vCardContent = readFileAsString(file);
            
            // Parse vCard
            VCardParser.SbmsMessage msg = VCardParser.parse(vCardContent);
            
            if (!msg.isMessage) {
                Log.d(TAG, "File is not a message, skipping");
                file.delete();
                return;
            }
            
            // Log parsed message
            Log.d(TAG, "Parsed message: " + msg);
            
            // TODO: Wire into SmsRelayService to send SMS
            // For now, just log
            
            // Delete processed file
            file.delete();
            Log.d(TAG, "Message processed and file deleted");
            
        } catch (Exception e) {
            Log.e(TAG, "Error processing message file: " + file.getName(), e);
        }
    }
    
    /**
     * Read file as string
     */
    private String readFileAsString(File file) throws IOException {
        FileInputStream fis = new FileInputStream(file);
        StringBuilder sb = new StringBuilder();
        byte[] buffer = new byte[1024];
        int length;
        while ((length = fis.read(buffer)) != -1) {
            sb.append(new String(buffer, 0, length, StandardCharsets.UTF_8));
        }
        fis.close();
        return sb.toString();
    }
}
