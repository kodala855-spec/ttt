# Android Kiosk Application

## Project Purpose

This is a minimal Android kiosk application designed to run a full-screen WebView in kiosk/locked-down mode. The application loads a configurable URL and provides comprehensive kiosk features including immersive fullscreen mode, hardware button lockdown, idle timeout, and runtime configuration via JSON.

**⚠️ Important Note:** No build has been performed in this repository. APK builds must be completed locally via Android Studio.

## Key Features

- **Full-screen WebView**: Displays web content in immersive fullscreen mode
- **Runtime Configuration**: Kiosk behavior configured via `kiosk_config.json` in app assets
- **Hardware Lockdown**: Disable back button, home button, and app switcher access
- **Idle Timeout**: Auto-restart after configurable inactivity period
- **Security**: Host whitelisting and external link blocking
- **Boot Auto-start**: BootReceiver automatically launches the app on device startup
- **Haptic & Visual Control**: Configurable haptic feedback and zoom controls

## Project Structure

```
.
├── README.md                                 # This file
├── CONFIGURATION.md                          # Detailed configuration schema
├── provision_adb.bat                         # Windows script to install APK via adb
├── app/
│   ├── build.gradle                          # App-level Gradle configuration
│   ├── proguard-rules.pro                    # ProGuard obfuscation rules
│   └── src/
│       ├── main/
│       │   ├── AndroidManifest.xml           # Android app manifest
│       │   ├── java/com/minimalkiosk/app/
│       │   │   ├── MainActivity.kt           # Main WebView activity with kiosk logic
│       │   │   └── BootReceiver.kt           # Broadcast receiver for boot events
│       │   ├── assets/
│       │   │   └── kiosk_config.json         # Runtime configuration file
│       │   └── res/                          # Android resources (layouts, strings, etc.)
├── build.gradle                              # Project-level Gradle configuration
├── gradle.properties                         # Gradle properties
├── gradlew                                   # Gradle wrapper (Unix)
├── settings.gradle                           # Gradle settings
└── .gitignore                                # Git ignore rules
```

## Prerequisites

- **Android Studio**: Installed on your development machine
- **Android SDK**: API level 33+ (Android 13+)
- **JDK**: Java Development Kit 11 or higher
- **ADB**: Android Debug Bridge (installed with Android Studio)
- **Windows (for provision_adb.bat)**: Or use equivalent adb commands on macOS/Linux

## Building the APK Locally

### Via Android Studio GUI

1. **Open the Project**
   - Launch Android Studio
   - Select "Open" and navigate to this repository directory
   - Click "Open"

2. **Let Gradle Sync**
   - Android Studio will automatically sync Gradle dependencies
   - Wait for the sync to complete (check the bottom status bar)

3. **Build the APK**
   - Go to **Build** > **Make Bundle/APK**
   - Select **Build APK(s)** from the menu
   - The build will compile and generate the APK

4. **Locate the Generated APK**
   - Navigate to: `app/build/outputs/apk/debug/app-debug.apk`
   - This is your ready-to-install APK file

### Via Command Line (Gradle)

```bash
# Navigate to the project root
cd /path/to/project

# Run the Gradle build
./gradlew assembleDebug

# APK will be available at: app/build/outputs/apk/debug/app-debug.apk
```

## Installing the APK on a Device

### Prerequisites for Installation

1. Enable **Developer Mode** on your Android device
   - Go to **Settings** > **About phone**
   - Tap **Build number** 7 times
   - Return to Settings to find **Developer options**

2. Enable **USB Debugging** in Developer options

3. Connect your device via USB cable

### Option 1: Using provision_adb.bat (Windows)

This script automates APK installation with optional optimizations:

```cmd
provision_adb.bat "path\to\app-debug.apk" device_id
```

**Example:**
```cmd
provision_adb.bat "C:\Users\user\project\app\build\outputs\apk\debug\app-debug.apk" emulator-5554
```

**Optional Flags:**
```cmd
provision_adb.bat "path\to\app.apk" device_id --disable-animations
provision_adb.bat "path\to\app.apk" device_id --disable-hints
```

### Option 2: Using ADB Directly

```bash
# Install APK (replace with your device ID and APK path)
adb -s <device_id> install -r app/build/outputs/apk/debug/app-debug.apk

# Example with emulator:
adb -s emulator-5554 install -r app/build/outputs/apk/debug/app-debug.apk

# Example with physical device:
adb -s 192.168.1.100:5555 install -r app/build/outputs/apk/debug/app-debug.apk
```

**Finding Device ID:**
```bash
adb devices
```

## Enabling Kiosk Mode on Device

Once the app is installed and running, configure it as a locked-down kiosk:

### Step 1: Grant Required Permissions

The app needs Device Administrator or System-level privileges for full lockdown. Depending on your device:

**Option A: Device Admin (Limited)**
- Open device **Settings** > **Apps** > **Special app access** > **Device admin apps**
- Find "Kiosk App" and grant Device Admin permission

**Option B: Kiosk Mode (Full - Recommended)**
- For devices with native kiosk mode support:
  - Open **Settings** > **Apps** > **Kiosk mode**
  - Enable the Kiosk App
  - Pin it as the default launcher

### Step 2: Make App the Default Launcher

1. Open **Settings** > **Apps** > **Default apps**
2. Set "Kiosk App" as the **Home/Launcher**
3. On boot, the app will automatically launch via BootReceiver

### Step 3: Verify Lockdown Features

Test that the following are disabled:
- **Back button**: Should not exit the app
- **Home button**: Should not show launcher
- **Recent apps**: Should not be accessible
- **Navigation buttons**: May be hidden in immersive mode

### Step 4: Disable System Features (Optional)

For complete kiosk lockdown, disable via ADB:

```bash
# Disable animations (for faster response)
adb shell settings put global animator_duration_scale 0

# Disable auto-start hints
adb shell settings put global setup_wizard_has_run 1

# Lock to portrait orientation (recommended for kiosks)
adb shell settings put system user_rotation 0

# Disable auto-brightness
adb shell settings put system screen_brightness_mode 0
adb shell settings put system screen_brightness 200
```

## Configuration

### Runtime Configuration via kiosk_config.json

The app loads configuration from `app/src/main/assets/kiosk_config.json`. Modify this file before building to customize:

- **URL**: Which website/web app to load
- **Idle Timeout**: Auto-restart duration
- **WebView Settings**: JavaScript, cache mode, zoom, DOM storage
- **Kiosk Mode Settings**: Button lockdown, screen behavior
- **Security**: Host whitelisting, external link blocking

**See `CONFIGURATION.md` for the complete schema and detailed options.**

### Key Configuration Example

```json
{
  "url": "https://example.com/kiosk",
  "idle_timeout_ms": 300000,
  "immersive_mode": true,
  "javascript_enabled": true,
  "kiosk_mode": {
    "disable_back_button": true,
    "disable_home_button": true,
    "disable_app_switch": true,
    "keep_screen_on": true
  },
  "security": {
    "allowed_hosts": ["example.com"],
    "block_external_links": true
  }
}
```

## Troubleshooting

### APK Installation Fails
- Ensure USB Debugging is enabled
- Run `adb devices` to verify device is connected
- Use `adb install -r` to replace an existing installation
- Check file path in `provision_adb.bat` is correct

### App Doesn't Start on Boot
- Verify BootReceiver is enabled in AndroidManifest.xml
- Make the app the default launcher in device settings
- Some custom Android ROMs may restrict boot receivers

### WebView Content Not Loading
- Verify the `url` in `kiosk_config.json` is accessible from the device
- Check network connectivity
- Enable JavaScript in `kiosk_config.json` if needed

### Buttons Still Work (Not Locked Down)
- Ensure Device Admin or Kiosk Mode permissions are granted
- Some ROM customizations may not support full lockdown
- Test on a stock Android device for best results

## Development

- **Language**: Kotlin
- **Target API**: Android 13+ (API 33+)
- **Build System**: Gradle
- **Key Libraries**: AndroidX AppCompat, WebView

## License

See LICENSE file for details.
