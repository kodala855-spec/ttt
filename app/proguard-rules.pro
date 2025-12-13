# Keep KioskActivity and related classes
-keep class com.example.kiosk.KioskActivity { *; }
-keep class com.example.kiosk.KioskConfig { *; }
-keep class com.example.kiosk.KioskAdminReceiver { *; }
-keep class com.example.kiosk.BootReceiver { *; }

# Keep AndroidX and AppCompat classes that might be used
-keep class androidx.appcompat.app.AppCompatActivity { *; }

# Keep JSON parsing classes
-keep class org.json.** { *; }

# Keep WebView related classes
-keep class android.webkit.** { *; }

# Remove logging in release builds
-assumenosideeffects class android.util.Log {
    public static boolean isLoggable(java.lang.String, int);
    public static int v(...);
    public static int i(...);
    public static int w(...);
    public static int d(...);
    public static int e(...);
}