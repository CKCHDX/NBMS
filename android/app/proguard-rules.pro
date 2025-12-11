# ProGuard rules for SBMS

# Keep all classes in com.ckchdx.sbms
-keep class com.ckchdx.sbms.** { *; }

# Keep all public classes
-keep public class * {
  public *** *;
}

# Keep all activity classes
-keep class * extends android.app.Activity
-keep class * extends android.app.Service
-keep class * extends android.content.BroadcastReceiver

# Keep enums
-keepclassmembers enum * {
    public static **[] values();
    public static ** valueOf(java.lang.String);
}

# Keep View constructors for inflation from XML
-keep class * extends android.view.View {
  public <init>(android.content.Context);
  public <init>(android.content.Context, android.util.AttributeSet);
  public <init>(android.content.Context, android.util.AttributeSet, int);
  public void set*(...);
}

# Keep Parcelable and Serializable
-keep class * implements android.os.Parcelable
-keep class * implements java.io.Serializable

# Keep data classes
-keepclassmembers class * {
    public *** component*();
    public *** copy(...);
    public *** copy$default(...);
}

# Timber logging
-assumenosideeffects class timber.log.Timber.* {
    public static *** v(...);
    public static *** d(...);
    public static *** i(...);
    public static *** w(...);
    public static *** e(...);
}

# Kotlin coroutines
-keepclassmembers class kotlinx.coroutines.** {
    <methods>;
}

# GSON
-keep class com.google.gson.** { *; }
-keep interface com.google.gson.** { *; }
