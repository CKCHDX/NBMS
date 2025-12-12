package com.oscyra.sbms.services;

import android.app.Service;
import android.content.Intent;
import android.os.Binder;
import android.os.IBinder;
import android.util.Log;

import androidx.annotation.Nullable;

public class SBMSMessageService extends Service {
    private static final String TAG = "SBMS_MessageService";
    private final IBinder binder = new LocalBinder();

    public class LocalBinder extends Binder {
        SBMSMessageService getService() {
            return SBMSMessageService.this;
        }
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Log.d(TAG, "SBMS Message Service started");
        return START_STICKY;
    }

    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        return binder;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        Log.d(TAG, "SBMS Message Service destroyed");
    }
}
