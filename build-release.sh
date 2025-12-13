#!/bin/bash
# Build and sign release APK for Kiosk WebView App
# Requires: JDK 17, Android SDK with API 34, build-tools 34.0.0

set -e  # Exit on error

echo "==============================================="
echo "Building Kiosk WebView App Release APK"
echo "==============================================="
echo ""

# Check prerequisites
if [ -z "$ANDROID_HOME" ]; then
    echo "❌ ERROR: ANDROID_HOME environment variable is not set"
    echo "   Please set it to your Android SDK directory"
    exit 1
fi

if ! command -v java &> /dev/null; then
    echo "❌ ERROR: Java is not installed or not in PATH"
    exit 1
fi

JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
if [ "$JAVA_VERSION" -lt 17 ]; then
    echo "❌ ERROR: Java 17 or higher is required (found version $JAVA_VERSION)"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Clean and build
echo "Step 1: Cleaning previous builds..."
./gradlew clean

echo ""
echo "Step 2: Building release APK..."
./gradlew assembleRelease

UNSIGNED_APK="app/build/outputs/apk/release/app-release-unsigned.apk"
ALIGNED_APK="app/build/outputs/apk/release/app-release-aligned.apk"
SIGNED_APK="app/build/outputs/apk/release/app-release.apk"

if [ ! -f "$UNSIGNED_APK" ]; then
    echo "❌ ERROR: Build failed - unsigned APK not found"
    exit 1
fi

echo "✅ Build successful"
echo ""

# Align APK
echo "Step 3: Aligning APK..."
$ANDROID_HOME/build-tools/34.0.0/zipalign -v -p 4 "$UNSIGNED_APK" "$ALIGNED_APK"

if [ ! -f "$ALIGNED_APK" ]; then
    echo "❌ ERROR: Alignment failed"
    exit 1
fi

echo "✅ APK aligned"
echo ""

# Sign APK
echo "Step 4: Signing APK..."

# Check if keystore exists
KEYSTORE="$HOME/.android/release.keystore"
if [ ! -f "$KEYSTORE" ]; then
    echo "⚠️  Keystore not found at $KEYSTORE"
    echo "   Creating a new keystore for testing..."
    keytool -genkey -v -keystore "$KEYSTORE" \
        -alias release -keyalg RSA -keysize 2048 -validity 10000 \
        -storepass android -keypass android \
        -dname "CN=Kiosk App, OU=Development, O=Example, L=City, S=State, C=US"
fi

$ANDROID_HOME/build-tools/34.0.0/apksigner sign \
    --ks "$KEYSTORE" \
    --ks-key-alias release \
    --ks-pass pass:android \
    --key-pass pass:android \
    --out "$SIGNED_APK" \
    "$ALIGNED_APK"

if [ ! -f "$SIGNED_APK" ]; then
    echo "❌ ERROR: Signing failed"
    exit 1
fi

echo "✅ APK signed"
echo ""

# Verify signature
echo "Step 5: Verifying signature..."
$ANDROID_HOME/build-tools/34.0.0/apksigner verify --verbose "$SIGNED_APK" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Signature verified"
else
    echo "❌ ERROR: Signature verification failed"
    exit 1
fi

echo ""

# Copy to artifacts
echo "Step 6: Copying to artifacts directory..."
mkdir -p artifacts
cp "$SIGNED_APK" artifacts/app-release.apk

# Generate checksum
cd artifacts
sha256sum app-release.apk > app-release.apk.sha256

APK_SIZE=$(ls -lh app-release.apk | awk '{print $5}')
CHECKSUM=$(cat app-release.apk.sha256 | awk '{print $1}')

echo "✅ APK copied to artifacts/"
echo ""

# Summary
echo "==============================================="
echo "Build Complete!"
echo "==============================================="
echo ""
echo "APK Details:"
echo "  Location: artifacts/app-release.apk"
echo "  Size: $APK_SIZE"
echo "  SHA256: $CHECKSUM"
echo ""
echo "To install on a device:"
echo "  adb install artifacts/app-release.apk"
echo ""
echo "To verify checksum:"
echo "  cd artifacts && sha256sum -c app-release.apk.sha256"
echo ""
