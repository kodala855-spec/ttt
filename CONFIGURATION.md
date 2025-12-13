# Kiosk App Configuration

## Overview

This Android kiosk application uses a JSON configuration file to manage its behavior and security settings. The configuration file is located at `app/src/main/assets/kiosk_config.json` and is loaded at runtime by `MainActivity`.

## Configuration Schema

### Required Fields

- **`url`** (string): The main URL to load in the WebView when the kiosk starts. This should be a fully qualified URL (e.g., `https://example.com/kiosk`).

### Optional Fields

#### WebView Configuration

- **`javascript_enabled`** (boolean, default: `true`): Enable/disable JavaScript execution in WebView. Most modern web apps require this to be true.
  - `true`: JavaScript is allowed
  - `false`: JavaScript is blocked

- **`cache_mode`** (string, default: `"no_cache"`): WebView cache behavior. Controls how the WebView caches resources.
  - `"no_cache"`: No caching, always fetch fresh content
  - `"default"`: Use default caching rules
  - `"cache_else_network"`: Use cache if available, otherwise fetch from network
  - `"cache_first"`: Use cache first, only fetch from network if not cached

- **`zoom_enabled`** (boolean, default: `false`): Enable/disable zoom controls in WebView. Disabling provides better kiosk experience.
  - `true`: User can pinch-to-zoom
  - `false`: Zoom controls are disabled

- **`dom_storage_enabled`** (boolean, default: `true`): Enable/disable DOM storage (localStorage) support. Required for web apps that store client-side data.
  - `true`: DOM storage is enabled
  - `false`: DOM storage is disabled

- **`haptic_feedback`** (boolean, default: `false`): Enable/disable haptic feedback (vibration) for long-press interactions. Kiosks typically disable this for user experience.
  - `true`: Haptic feedback is enabled
  - `false`: Haptic feedback is disabled

#### UI and Immersive Mode

- **`immersive_mode`** (boolean, default: `true`): Enable/disable immersive fullscreen mode. Hides system UI elements for a cleaner kiosk display.
  - `true`: System UI is hidden, content takes full screen
  - `false`: Standard Android UI elements are shown

#### Idle Timeout

- **`idle_timeout_ms`** (integer, default: `300000` (5 minutes)): Inactivity timeout in milliseconds. After this duration without user interaction, the app will reload/restart.
  - Value in milliseconds (e.g., `300000` = 5 minutes, `600000` = 10 minutes)
  - Set to `0` to disable idle timeout

#### Kiosk Mode Settings

- **`kiosk_mode`** (object): Container for kiosk-specific restrictions and behaviors.

  - **`disable_back_button`** (boolean, default: `true`): Prevent the back button from exiting the app or navigating backward.
    - `true`: Back button is disabled
    - `false`: Back button functions normally

  - **`disable_home_button`** (boolean, default: `true`): Prevent the home button from accessing the launcher or home screen.
    - `true`: Home button access is blocked
    - `false`: Home button functions normally

  - **`disable_app_switch`** (boolean, default: `true`): Prevent access to recent apps or app switcher.
    - `true`: App switcher is disabled
    - `false`: App switcher functions normally

  - **`keep_screen_on`** (boolean, default: `true`): Keep the screen always on and prevent screen timeout.
    - `true`: Screen stays on indefinitely
    - `false`: Screen can timeout based on system settings

#### Security Settings

- **`security`** (object): Container for security-related configurations.

  - **`allowed_hosts`** (array of strings, default: `[]`): Whitelist of allowed hostnames. Leave empty to allow all hosts.
    - Examples: `["example.com", "cdn.example.com", "api.example.com"]`
    - If not empty, only these domains can be loaded in the WebView
    - Restricts security if navigation is attempted to unauthorized hosts

  - **`block_external_links`** (boolean, default: `true`): Block external links from opening in external browsers.
    - `true`: External links are blocked or opened in the same WebView
    - `false`: External links open in the device's default browser

#### Future Extensions

- **`future_extensions`** (object): Placeholder for future configuration options. Current fields for documentation:

  - **`night_mode`** (boolean, default: `false`): Placeholder for night mode support (not yet implemented).
  
  - **`orientation_lock`** (string, default: `"portrait"`): Placeholder for screen orientation locking (not yet implemented).
    - `"portrait"`: Lock to portrait orientation
    - `"landscape"`: Lock to landscape orientation
    - `"auto"`: Allow automatic rotation
  
  - **`volume_locked`** (boolean, default: `false`): Placeholder for volume control lockdown (not yet implemented).
    - `true`: Volume buttons would be disabled
    - `false`: Volume buttons function normally
  
  - **`status_bar_hidden`** (boolean, default: `true`): Placeholder for status bar visibility control (not yet implemented).
    - `true`: Status bar is hidden
    - `false`: Status bar is visible

## Example Configuration

```json
{
  "url": "https://www.napolyane.com/menu-restaurant",
  "idle_timeout_ms": 300000,
  "immersive_mode": true,
  "haptic_feedback": false,
  "javascript_enabled": true,
  "cache_mode": "no_cache",
  "zoom_enabled": false,
  "dom_storage_enabled": true,
  "kiosk_mode": {
    "disable_back_button": true,
    "disable_home_button": true,
    "disable_app_switch": true,
    "keep_screen_on": true
  },
  "security": {
    "allowed_hosts": [],
    "block_external_links": true
  },
  "future_extensions": {
    "night_mode": false,
    "orientation_lock": "portrait",
    "volume_locked": false,
    "status_bar_hidden": true
  }
}
```

## Minimal Configuration

If you only need to specify the URL, you can use this minimal config:

```json
{
  "url": "https://example.com"
}
```

All other settings will use their defaults.

## Editing Configuration

### Before Building

1. Edit `app/src/main/assets/kiosk_config.json`
2. Rebuild the APK using Android Studio or Gradle
3. Reinstall the APK on your device

### At Runtime

To modify configuration after APK installation:

1. Edit the `kiosk_config.json` file on the device's storage (if you extract and re-package it)
2. OR rebuild and reinstall the APK with new config

Note: The configuration is baked into the APK during build. To update it without rebuilding, more advanced techniques (like downloading config from a remote server) would be needed.

## Common Configuration Scenarios

### Restaurant Menu Kiosk

```json
{
  "url": "https://menu.restaurant.com/kiosk",
  "idle_timeout_ms": 120000,
  "immersive_mode": true,
  "javascript_enabled": true,
  "cache_mode": "cache_else_network",
  "zoom_enabled": false,
  "dom_storage_enabled": true,
  "kiosk_mode": {
    "disable_back_button": true,
    "disable_home_button": true,
    "disable_app_switch": true,
    "keep_screen_on": true
  },
  "security": {
    "allowed_hosts": ["menu.restaurant.com"],
    "block_external_links": true
  }
}
```

### Information Display Kiosk

```json
{
  "url": "https://info.example.com/display",
  "idle_timeout_ms": 600000,
  "immersive_mode": true,
  "javascript_enabled": true,
  "cache_mode": "default",
  "zoom_enabled": false,
  "dom_storage_enabled": false,
  "kiosk_mode": {
    "disable_back_button": true,
    "disable_home_button": true,
    "disable_app_switch": true,
    "keep_screen_on": true
  },
  "security": {
    "allowed_hosts": [],
    "block_external_links": false
  }
}
```

### High-Security Kiosk

```json
{
  "url": "https://secure.example.com/kiosk",
  "idle_timeout_ms": 180000,
  "immersive_mode": true,
  "javascript_enabled": false,
  "cache_mode": "no_cache",
  "zoom_enabled": false,
  "dom_storage_enabled": false,
  "kiosk_mode": {
    "disable_back_button": true,
    "disable_home_button": true,
    "disable_app_switch": true,
    "keep_screen_on": true
  },
  "security": {
    "allowed_hosts": ["secure.example.com"],
    "block_external_links": true
  }
}
```

## Troubleshooting Configuration Issues

### Configuration Not Loading

- Check JSON syntax (use a JSON validator)
- Verify file location: `app/src/main/assets/kiosk_config.json`
- Check build logs for parsing errors
- Application falls back to defaults if file is malformed

### Changes Not Taking Effect

- Configuration is loaded at app startup
- Kill and restart the app to reload config
- Or rebuild and reinstall the APK
- Check app logs: `adb logcat | grep minimalkiosk`

### WebView Issues

- If `javascript_enabled: false`, many modern web apps won't work
- If `cache_mode: "no_cache"`, performance may suffer
- If `zoom_enabled: true`, users can zoom, breaking kiosk UX
- If `dom_storage_enabled: false`, web apps using localStorage will fail

### Security Issues

- `allowed_hosts: []` allows ALL hosts (use with caution)
- `block_external_links: false` allows breaking out to other apps
- For high-security environments, restrict to specific domains
