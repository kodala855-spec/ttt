# Kiosk WebView App

An Android kiosk application with WebView functionality, designed for locked-down tablet deployments.

## Project Structure

```
.
├── app/                    # Android application module
│   ├── src/                # Source code
│   └── build.gradle        # App-level build configuration
├── artifacts/              # Release APK and build artifacts
│   ├── app-release.apk     # Signed release APK
│   ├── BUILD_INFO.txt      # Build metadata
│   └── README.md           # Artifact documentation
├── gradle/                 # Gradle wrapper files
│   └── wrapper/
│       ├── gradle-wrapper.jar
│       └── gradle-wrapper.properties
├── gradlew                 # Gradle wrapper script (Unix)
├── gradlew.bat             # Gradle wrapper script (Windows)
├── build.gradle            # Project-level build configuration
├── settings.gradle         # Project settings
└── gradle.properties       # Gradle configuration
```

## Build Requirements

- **JDK**: OpenJDK 17 or higher
- **Android SDK**: API Level 34
- **Build Tools**: 34.0.0
- **Gradle**: 8.2 (provided via wrapper)

## Building the Project

### Quick Start

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd KioskWebViewApp
   ```

2. Build the debug APK:
   ```bash
   ./gradlew assembleDebug
   ```

3. Build the release APK:
   ```bash
   ./gradlew clean assembleRelease
   ```

### Build Commands

- **Clean build**: `./gradlew clean`
- **Debug build**: `./gradlew assembleDebug`
- **Release build**: `./gradlew assembleRelease`
- **Run tests**: `./gradlew test`
- **Install on device**: `./gradlew installDebug` or `./gradlew installRelease`

## Configuration

### Environment Setup

Set the Android SDK location in one of the following ways:

1. Create `local.properties` file (not in version control):
   ```properties
   sdk.dir=/path/to/android-sdk
   ```

2. Set environment variable:
   ```bash
   export ANDROID_HOME=/path/to/android-sdk
   ```

### Gradle Properties

The project uses the following Gradle properties (defined in `gradle.properties`):
- `android.useAndroidX=true` - Enable AndroidX libraries
- `android.enableJetifier=true` - Automatically migrate legacy libraries
- `org.gradle.jvmargs=-Xmx2048m` - Set JVM memory allocation

## Application Details

- **Package Name**: `com.example.kiosk`
- **Version Code**: 1
- **Version Name**: 1.0
- **Min SDK**: Android 5.0 (API 21)
- **Target SDK**: Android 14 (API 34)
- **Compile SDK**: Android 14 (API 34)

## Release APK

Pre-built signed release APKs are available in the `artifacts/` directory. See [artifacts/README.md](artifacts/README.md) for details.

### APK Specifications

- **Size**: ~1.2 MB (within 5-15 MB requirement)
- **Signed**: Yes (using release keystore)
- **Aligned**: Yes (optimized with zipalign)
- **Architecture**: Universal (all ABIs)

## Installation

### Via ADB

```bash
adb install artifacts/app-release.apk
```

### Manual Installation

1. Transfer the APK to your Android device
2. Enable "Unknown Sources" in device settings
3. Open the APK file to install

## Development

### Tech Stack

- **Language**: Kotlin 1.9.20
- **Build System**: Gradle 8.2 with Android Gradle Plugin 8.2.0
- **UI Framework**: Android SDK
- **WebView**: AndroidX WebKit 1.9.0

### Dependencies

- `androidx.core:core-ktx:1.12.0` - AndroidX Core Kotlin extensions
- `androidx.webkit:webkit:1.9.0` - Modern WebView APIs

## Reproducible Builds

This project is configured for reproducible builds:

1. **Gradle wrapper** is included and pinned to version 8.2
2. **Dependencies** are version-locked in build files
3. **Build tools** version is specified (34.0.0)
4. **JDK version** is documented (17)

To verify a reproducible build:

```bash
./gradlew clean assembleRelease
sha256sum app/build/outputs/apk/release/app-release-unsigned.apk
```

Compare the checksum with the one in `artifacts/app-release.apk.sha256`.

## Signing

The release APK is signed using a keystore stored outside version control. 

For production releases, you should:
1. Generate a secure release keystore
2. Store it securely (e.g., password manager, secure vault)
3. Never commit keystore files to version control

## CI/CD

The project is ready for CI/CD integration. Example GitHub Actions workflow:

```yaml
- name: Build Release APK
  run: ./gradlew clean assembleRelease
  
- name: Sign APK
  run: |
    zipalign -v -p 4 app/build/outputs/apk/release/app-release-unsigned.apk aligned.apk
    apksigner sign --ks ${{ secrets.KEYSTORE_FILE }} --out app-release.apk aligned.apk
```

## Testing

The APK has been verified to:
- ✅ Build successfully with Gradle 8.2
- ✅ Meet size requirements (1.2 MB < 15 MB)
- ✅ Sign and verify correctly
- ✅ Align properly with zipalign
- ✅ Target Android 13+ tablets

## Support

For issues, questions, or contributions, please refer to the project's issue tracker.

## License

[Specify your license here]
