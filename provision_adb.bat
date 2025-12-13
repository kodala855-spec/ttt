@echo off
REM provision_adb.bat - Automated APK Installation Script
REM
REM Purpose: Install APK file on Android device/emulator via adb
REM
REM Usage:
REM   provision_adb.bat "path\to\app.apk" device_id [--disable-animations] [--disable-hints]
REM
REM Examples:
REM   provision_adb.bat "app\build\outputs\apk\debug\app-debug.apk" emulator-5554
REM   provision_adb.bat "C:\Users\user\app.apk" device_id --disable-animations
REM   provision_adb.bat "app.apk" 192.168.1.100:5555 --disable-hints
REM
REM Arguments:
REM   path                - Full or relative path to the APK file
REM   device_id           - Device ID (from 'adb devices')
REM   --disable-animations - (Optional) Disable system animations for faster response
REM   --disable-hints      - (Optional) Disable auto-start hints
REM

setlocal enabledelayedexpansion

REM Check arguments
if "%~1"=="" (
    echo Error: APK path is required
    echo Usage: provision_adb.bat "path\to\app.apk" device_id [--disable-animations] [--disable-hints]
    exit /b 1
)

if "%~2"=="" (
    echo Error: Device ID is required
    echo Usage: provision_adb.bat "path\to\app.apk" device_id [--disable-animations] [--disable-hints]
    exit /b 1
)

set APK_PATH=%~1
set DEVICE_ID=%~2
set DISABLE_ANIMATIONS=false
set DISABLE_HINTS=false

REM Parse optional flags
if not "%~3"=="" (
    if "%~3"=="--disable-animations" set DISABLE_ANIMATIONS=true
    if "%~3"=="--disable-hints" set DISABLE_HINTS=true
)

if not "%~4"=="" (
    if "%~4"=="--disable-animations" set DISABLE_ANIMATIONS=true
    if "%~4"=="--disable-hints" set DISABLE_HINTS=true
)

REM Verify APK file exists
if not exist "%APK_PATH%" (
    echo Error: APK file not found: %APK_PATH%
    exit /b 1
)

echo.
echo ========================================
echo Kiosk APK Installation Script
echo ========================================
echo.
echo APK Path:       %APK_PATH%
echo Device ID:      %DEVICE_ID%
echo Disable Anims:  %DISABLE_ANIMATIONS%
echo Disable Hints:  %DISABLE_HINTS%
echo.

REM Check if device is connected
echo [*] Checking device connection...
adb -s %DEVICE_ID% shell getprop ro.build.version.release > nul 2>&1
if !errorlevel! neq 0 (
    echo Error: Device '%DEVICE_ID%' not found or offline
    echo.
    echo Available devices:
    adb devices
    exit /b 1
)

echo [✓] Device connected
echo.

REM Install APK with -r flag (replace existing)
echo [*] Installing APK...
adb -s %DEVICE_ID% install -r "%APK_PATH%"
if !errorlevel! neq 0 (
    echo Error: Failed to install APK
    exit /b 1
)

echo [✓] APK installed successfully
echo.

REM Optional: Disable animations for faster response
if "%DISABLE_ANIMATIONS%"=="true" (
    echo [*] Disabling system animations...
    adb -s %DEVICE_ID% shell settings put global animator_duration_scale 0
    if !errorlevel! equ 0 (
        echo [✓] Animations disabled
    ) else (
        echo [!] Failed to disable animations (non-critical)
    )
    echo.
)

REM Optional: Disable auto-start hints
if "%DISABLE_HINTS%"=="true" (
    echo [*] Disabling auto-start hints...
    adb -s %DEVICE_ID% shell settings put global setup_wizard_has_run 1
    if !errorlevel! equ 0 (
        echo [✓] Setup wizard hidden
    ) else (
        echo [!] Failed to disable hints (non-critical)
    )
    echo.
)

REM Optional: Bring app to foreground
echo [*] Launching application...
adb -s %DEVICE_ID% shell am start -n com.minimalkiosk.app/.MainActivity 2>&1 | find "Error" > nul
if !errorlevel! equ 0 (
    echo [!] Could not launch app (may not be installed or app package name differs)
) else (
    echo [✓] Application started
)

echo.
echo ========================================
echo Installation Complete
echo ========================================
echo.
echo Next steps:
echo 1. Enable Developer Mode on device:
echo    Settings ^> About phone ^> tap Build number 7 times
echo 2. Enable USB Debugging:
echo    Settings ^> Developer options ^> USB Debugging
echo 3. Make app the default launcher:
echo    Settings ^> Apps ^> Default apps ^> Home ^> Kiosk App
echo 4. For full lockdown, grant Device Admin or Kiosk Mode permissions
echo.

exit /b 0
