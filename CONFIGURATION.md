# Kiosk App Configuration

## Overview

This Android kiosk application uses a JSON configuration file to manage its behavior and security settings. The configuration file is located at `app/src/main/assets/kiosk_config.json` and is loaded at runtime by `MainActivity`.

## Configuration Schema

### Required Fields

- **`url`** (string): The main URL to load in the WebView when the kiosk starts.

### Optional Fields

#### WebView Configuration
- **`javascript_enabled`** (boolean, default: `true`): Enable/disable JavaScript execution in WebView.
- **`cache_mode`** (string, default: `"no_cache"`): WebView cache behavior. Options: `"no_cache"`, `"default"`, `"cache_else_network"`, `"cache_first"`.
- **`zoom_enabled`** (boolean, default: `false`): Enable/disable zoom controls in WebView.
- **`dom_storage_enabled`** (boolean, default: `true`): Enable/disable DOM storage support.
- **`haptic_feedback`** (boolean, default: `false`): Enable/disable haptic feedback for long-press interactions.

#### UI and Immersive Mode
- **`immersive_mode`** (boolean, default: `true`): Enable fullscreen immersive mode to hide system bars.
- **`idle_timeout_ms`** (integer, default: `300000`): Idle timeout in milliseconds before kiosk restarts (5 minutes).

#### Kiosk Mode Settings
- **`kiosk_mode`** (object): Security settings for kiosk behavior:
  - **`disable_back_button`** (boolean, default: `true`): Prevent back button from exiting app.
  - **`disable_home_button`** (boolean, default: `true`): Prevent home button access.
  - **`disable_app_switch`** (boolean, default: `true`): Prevent app switcher access.
  - **`keep_screen_on`** (boolean, default: `true`): Keep screen always on to prevent sleep.

#### Security and URL Filtering
- **`security`** (object): Security and URL filtering settings:
  - **`allowed_hosts`** (array, default: `[]`): Whitelist of allowed hostnames. Empty array allows all hosts.
  - **`block_external_links`** (boolean, default: `true`): Block external links from opening in external browsers.

#### Future Extensions
- **`future_extensions`** (object): Placeholder for future configuration options:
  - **`night_mode`** (boolean, default: `false`): Enable dark/night mode for the interface.
  - **`orientation_lock`** (string, default: `"portrait"`): Lock screen orientation. Options: `"portrait"`, `"landscape"`, `"auto"`.
  - **`volume_locked`** (boolean, default: `false`): Lock volume controls to prevent user adjustment.
  - **`status_bar_hidden`** (boolean, default: `true`): Hide status bar for enhanced kiosk experience.

## Default Configuration

If the configuration file is missing or malformed, the application falls back to these defaults:

- URL: `"https://www.napolyane.com/menu-restaurant"`
- All other settings use the default values specified in the schema above

## Loading the Configuration

The `MainActivity` class loads the configuration using `assets.open("kiosk_config.json")` and parses it as JSON. The configuration is loaded once when the activity is created and applies settings throughout the application lifecycle.

## Usage

1. **Basic Setup**: Update the `url` field with your desired kiosk URL.
2. **Customize Behavior**: Adjust WebView, kiosk mode, and security settings as needed.
3. **Security**: Configure `allowed_hosts` to restrict navigation to specific domains.
4. **UI Preferences**: Enable/disable immersive mode, zoom controls, and other interface elements.

## Future Development

The configuration schema is designed to be extensible. New features can be added to the `future_extensions` section without breaking existing deployments. Developers should document new configuration options in this section as the kiosk evolves.

## Schema Evolution

When adding new configuration options:
1. Add them to the appropriate section in `kiosk_config.json`
2. Update this README with the new option documentation
3. Modify `MainActivity` to handle the new configuration option
4. Ensure backward compatibility with existing configurations