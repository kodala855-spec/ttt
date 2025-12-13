# Kiosk App Installation Guide

This guide describes how to deploy the Kiosk application to Android 13 tablets using ADB (Android Debug Bridge).

## Prerequisites

Before proceeding, ensure you have the following:

1.  **Hardware**: An Android 13 tablet and a USB cable.
2.  **Software**:
    *   [Android Platform Tools](https://developer.android.com/studio/releases/platform-tools) installed on your computer (specifically `adb`).
    *   The release APK file (`app-release.apk`).

## Setup

### 1. Enable USB Debugging on the Tablet

1.  Go to **Settings > About tablet**.
2.  Tap **Build number** 7 times to enable Developer Options.
3.  Go back to **Settings > System > Developer options**.
4.  Enable **USB debugging**.

### 2. Connect the Device

1.  Connect the tablet to your computer via USB.
2.  On your computer, open a terminal/command prompt.
3.  Run the following command to verify the connection:
    ```bash
    adb devices
    ```
4.  Look for your device in the list. It should look like this:
    ```
    List of devices attached
    12345678    device
    ```
    *   If the status is `unauthorized`, look at your tablet screen and accept the USB debugging prompt.

## Obtaining the APK

The release artifact `app-release.apk` can be found in the `artifacts/` directory of this repository.

If you are downloading it from a CI/CD pipeline or Releases page, ensure you place it in an `artifacts/` directory or adjust the installation path accordingly.

## Installation

To install or update the application, run the following command from the repository root:

```bash
adb install -r artifacts/app-release.apk
```

*   The `-r` flag allows re-installing the app if it is already installed (keeping its data).

### Expected Output

If the installation is successful, you will see:

```
Performing Streamed Install
Success
```

## Verification

To verify that the application has been installed correctly, run:

```bash
adb shell pm list packages | grep com.example.kiosk
```

You should see the following output:

```
package:com.example.kiosk
```

## Troubleshooting

*   **Device not found**: Ensure USB debugging is enabled and the cable is securely connected. Try running `adb kill-server` followed by `adb start-server`.
*   **Unauthorized**: Check the tablet screen for a confirmation dialog to trust the computer.
*   **Install failed**: If you get an error like `INSTALL_FAILED_UPDATE_INCOMPATIBLE`, you may need to uninstall the old version first:
    ```bash
    adb uninstall com.example.kiosk
    ```
    Then try installing again.
