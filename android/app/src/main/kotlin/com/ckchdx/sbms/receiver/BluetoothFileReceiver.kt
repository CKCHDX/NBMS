package com.ckchdx.sbms.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.ckchdx.sbms.service.SBMSBluetoothService

/**
 * Broadcast Receiver for Bluetooth File Events
 *
 * Listens for:
 * - MEDIA_SCANNER_FINISHED (when files are added to Bluetooth folder)
 * - BLUETOOTH file transfer events
 *
 * This ensures immediate processing of incoming Bluetooth OPP files
 * without waiting for the polling interval in SBMSBluetoothService
 */
class BluetoothFileReceiver : BroadcastReceiver() {

    companion object {
        private const val TAG = "BluetoothFileReceiver"
    }

    override fun onReceive(context: Context, intent: Intent?) {
        if (intent == null) return

        Log.d(TAG, "Broadcast received: ${intent.action}")

        when (intent.action) {
            Intent.ACTION_MEDIA_SCANNER_FINISHED -> {
                // Media scanner finished - likely new files in Bluetooth folder
                Log.i(TAG, "Media scanner finished, triggering service")
                triggerBluetoothService(context)
            }
            "android.intent.action.MEDIA_MOUNTED" -> {
                Log.i(TAG, "Media mounted, triggering service")
                triggerBluetoothService(context)
            }
        }
    }

    /**
     * Trigger the SBMS Bluetooth Service to scan for new files
     */
    private fun triggerBluetoothService(context: Context) {
        try {
            val serviceIntent = Intent(context, SBMSBluetoothService::class.java)
            context.startService(serviceIntent)
            Log.d(TAG, "Service triggered")
        } catch (e: Exception) {
            Log.e(TAG, "Error triggering service", e)
        }
    }
}
