# KioskWebViewApp

An Android kiosk application built with Kotlin and Jetpack Compose.

## Requirements

- Android SDK (API 21+)
- Kotlin 1.9.20
- Gradle 8.x
- Android Studio (recommended for development)

## Building

To build the APK release:

```bash
./gradlew assembleRelease
```

The built APK will be located at `artifacts/app-release.apk`.

## Provisioning Tablets (Windows)

### Prerequisites

1. **Android SDK Platform Tools**: Install the Android SDK Platform Tools which includes `adb.exe`
   - Download from: https://developer.android.com/tools/releases/platform-tools
   - Or install via Android Studio's SDK Manager
   - Ensure `adb.exe` is in your system PATH

2. **USB Drivers**: Install appropriate USB drivers for your Android tablets

3. **Build the APK**: Run `./gradlew assembleRelease` to create the APK file

### Installing APK to Tablets

#### Method 1: Double-click the Script (Easiest)
1. Connect your Android tablets via USB
2. Enable USB Debugging on each tablet (Settings > Developer Options > USB Debugging)
3. Double-click `provision_apk.bat` at the repository root
4. The script will automatically detect all connected devices and install the APK on each

#### Method 2: Run from PowerShell or Command Prompt
1. Open PowerShell or Command Prompt
2. Navigate to the repository root directory
3. Run:
   ```powershell
   .\provision_apk.bat
   ```
   or
   ```cmd
   provision_apk.bat
   ```

### What the Script Does

The `provision_apk.bat` script:
- Verifies that `adb.exe` is available in the system PATH
- Confirms the APK file exists at `artifacts/app-release.apk`
- Lists all connected Android devices
- Installs the APK on each connected device using `adb install -r` (with reinstall flag)
- Provides clear success/failure messaging for each device
- Returns appropriate exit codes for error handling

### Error Handling

The script handles the following error cases:

- **adb.exe not found**: Exits with code 1, prompts to install Android SDK Platform Tools
- **APK file missing**: Exits with code 1, prompts to build the APK first
- **No devices connected**: Exits with code 1, prompts to connect at least one device
- **Installation failures**: Exits with code 1 and lists which devices failed

### Troubleshooting

**"adb.exe not found in PATH"**
- Install Android SDK Platform Tools
- Add the installation directory to your system PATH environment variable
- Restart your terminal/PowerShell window

**"artifacts\app-release.apk not found"**
- Build the APK by running `./gradlew assembleRelease` in the repository root

**"No devices found"**
- Ensure tablets are connected via USB
- Check that USB Debugging is enabled on each tablet
- Run `adb devices` in PowerShell/Command Prompt to verify connectivity

**Installation fails on specific devices**
- Ensure the device has sufficient storage space
- Check that the device's USB connection is stable
- Try unplugging and reconnecting the device
- Enable developer options and verify USB Debugging is still enabled

## Development

For local development, use Android Studio to open the project and run it on an emulator or connected device.

### Project Structure

- `/app` - Main application module
- `/build.gradle` - Root build configuration
- `/settings.gradle` - Gradle settings

## License

[License information if applicable]
