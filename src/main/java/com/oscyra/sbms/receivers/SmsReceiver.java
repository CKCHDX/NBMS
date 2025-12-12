package com.oscyra.sbms.receivers;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.telephony.SmsMessage;
import android.util.Log;

import com.oscyra.sbms.MainActivity;

public class SmsReceiver extends BroadcastReceiver {
    private static final String TAG = "SBMS_SmsReceiver";
    private static final String SMS_RECEIVED = "android.provider.Telephony.SMS_RECEIVED";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent.getAction() == null || !intent.getAction().equals(SMS_RECEIVED)) {
            return;
        }

        Bundle bundle = intent.getExtras();
        if (bundle == null) {
            return;
        }

        Object[] pdus = (Object[]) bundle.get("pdus");
        if (pdus == null || pdus.length == 0) {
            return;
        }

        for (Object pdu : pdus) {
            SmsMessage smsMessage;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                smsMessage = SmsMessage.createFromPdu((byte[]) pdu, "3gpp");
            } else {
                smsMessage = SmsMessage.createFromPdu((byte[]) pdu);
            }

            String sender = smsMessage.getOriginatingAddress();
            String body = smsMessage.getMessageBody();
            long timestamp = smsMessage.getTimestampMillis();

            Log.d(TAG, "SMS received from: " + sender + " | " + body);

            // Handle received SMS - notify MainActivity or database
            Intent broadcastIntent = new Intent("com.oscyra.sbms.SMS_RECEIVED");
            broadcastIntent.putExtra("sender", sender);
            broadcastIntent.putExtra("body", body);
            broadcastIntent.putExtra("timestamp", timestamp);
            context.sendBroadcast(broadcastIntent);
        }
    }
}
