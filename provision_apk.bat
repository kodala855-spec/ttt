@echo off
setlocal enabledelayedexpansion

REM Windows installer script to provision the APK to all connected Android tablets
REM This script installs artifacts\app-release.apk to all connected devices via ADB

REM Check if adb.exe is available
where adb.exe >nul 2>nul
if errorlevel 1 (
    echo Error: adb.exe not found in PATH. Please install Android SDK Platform Tools.
    exit /b 1
)

REM Check if APK file exists
if not exist "artifacts\app-release.apk" (
    echo Error: artifacts\app-release.apk not found. Please build the APK first.
    exit /b 1
)

echo.
echo ========================================
echo Android APK Provisioning Script
echo ========================================
echo.
echo APK: artifacts\app-release.apk
echo.

REM Get list of connected devices
echo Scanning for connected devices...
echo.

adb devices > "%temp%\adb_devices.txt"

REM Parse devices and skip header line
set device_count=0
set error_count=0

for /f "skip=1 tokens=1" %%A in (%temp%\adb_devices.txt) do (
    set device=%%A
    
    REM Skip empty lines and "List of attached devices" header
    if not "!device!"=="" if not "!device!"=="List" (
        set /a device_count+=1
        echo.
        echo [!device_count!] Installing on device: !device!
        
        adb -s !device! install -r artifacts\app-release.apk
        
        if errorlevel 1 (
            echo.
            echo ERROR: Failed to install APK on device !device!
            set /a error_count+=1
        ) else (
            echo.
            echo SUCCESS: APK installed on device !device!
        )
    )
)

REM Clean up temp file
del "%temp%\adb_devices.txt" 2>nul

echo.
echo ========================================
echo Installation Summary
echo ========================================
echo Total devices processed: !device_count!
set /a success_count=device_count-error_count
echo Successful installations: !success_count!
echo Failed installations: !error_count!
echo.

if !device_count! equ 0 (
    echo Error: No devices found. Please connect at least one device.
    exit /b 1
)

if !error_count! gtr 0 (
    echo Warning: Some installations failed. Please check the errors above.
    exit /b 1
)

echo All devices provisioned successfully!
exit /b 0
