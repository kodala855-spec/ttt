# Release Artifacts

This directory contains the signed release APK for the Kiosk WebView App.

## Files

- **app-release.apk** - Signed and aligned release APK ready for installation
- **app-release.apk.sha256** - SHA256 checksum for verifying APK integrity
- **BUILD_INFO.txt** - Detailed build information and metadata

## Building the Release APK

To build the release APK from source, follow these steps:

### Prerequisites

- JDK 17 (OpenJDK recommended)
- Android SDK with API 34 and Build Tools 34.0.0
- Gradle 8.2 (included via Gradle wrapper)

### Build Steps

1. Clone the repository
2. Ensure you have set `ANDROID_HOME` environment variable pointing to your Android SDK
3. Run the following command:
   ```bash
   ./gradlew clean assembleRelease
   ```
4. The unsigned APK will be generated at: `app/build/outputs/apk/release/app-release-unsigned.apk`

### Signing the APK

To sign and align the APK:

1. **Align the APK:**
   ```bash
   zipalign -v -p 4 app/build/outputs/apk/release/app-release-unsigned.apk \
     app/build/outputs/apk/release/app-release-aligned.apk
   ```

2. **Sign the APK:**
   ```bash
   apksigner sign --ks /path/to/keystore.keystore --ks-key-alias your-alias \
     --out app/build/outputs/apk/release/app-release.apk \
     app/build/outputs/apk/release/app-release-aligned.apk
   ```

3. **Verify the signature:**
   ```bash
   apksigner verify --verbose app/build/outputs/apk/release/app-release.apk
   ```

## Installation

To install the APK on an Android device:

```bash
adb install artifacts/app-release.apk
```

Or transfer the APK to your device and install it manually.

## Verification

To verify the APK integrity, use the provided checksum:

```bash
sha256sum -c app-release.apk.sha256
```

## APK Requirements

- **Size**: 1.2 MB (well within the 5-15 MB requirement)
- **Min SDK**: Android 5.0 (API 21)
- **Target SDK**: Android 14 (API 34)
- **Permissions**: Internet access for WebView functionality
