# ProGuard rules for SBMS Android App

# Keep application classes
-keep class com.oscyra.sbms.** { *; }

# Keep Android framework classes
-keep class android.** { *; }

# Keep Bluetooth related classes
-keep class android.bluetooth.** { *; }

# Keep Room database classes
-keep class androidx.room.** { *; }
-keep @androidx.room.Entity class * { *; }
-keep @androidx.room.Dao interface * { *; }

# Keep callback interfaces
-keep interface com.oscyra.sbms.bluetooth.BluetoothManager$** { *; }

# Preserve line numbers for debugging
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile
