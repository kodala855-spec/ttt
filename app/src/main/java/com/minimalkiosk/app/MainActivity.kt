package com.minimalkiosk.app

import android.os.Bundle
import android.view.KeyEvent
import android.view.ViewGroup
import android.view.WindowManager
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import org.json.JSONArray
import org.json.JSONObject
import android.os.Handler
import android.os.Looper
import kotlin.system.exitProcess

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView
    private var config: JSONObject = JSONObject()
    private var idleTimeoutRunnable: Runnable? = null
    private val handler = Handler(Looper.getMainLooper())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        loadConfiguration()
        
        webView = WebView(this).apply {
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
        }
        setContentView(webView)

        applyKioskSettings()
        configureWebView()
        
        // Start with initial URL load
        resetIdleTimeout()
        webView.loadUrl(config.optString("url", ""))
    }

    /**
     * Load kiosk configuration from assets/kiosk_config.json
     * Falls back to defaults if file is missing or malformed
     */
    private fun loadConfiguration() {
        config = runCatching {
            val raw = assets.open("kiosk_config.json").bufferedReader().use { it.readText() }
            JSONObject(raw)
        }.getOrDefault(JSONObject().apply {
            put("url", "https://www.napolyane.com/menu-restaurant")
            put("idle_timeout_ms", 300000)
            put("immersive_mode", true)
            put("haptic_feedback", false)
            put("javascript_enabled", true)
            put("cache_mode", "no_cache")
            put("zoom_enabled", false)
            put("dom_storage_enabled", true)
            put("kiosk_mode", JSONObject().apply {
                put("disable_back_button", true)
                put("disable_home_button", true)
                put("disable_app_switch", true)
                put("keep_screen_on", true)
            })
            put("security", JSONObject().apply {
                put("allowed_hosts", JSONArray())
                put("block_external_links", true)
            })
            put("future_extensions", JSONObject())
        })
    }

    /**
     * Apply kiosk-specific settings based on configuration
     */
    private fun applyKioskSettings() {
        val kioskMode = config.optJSONObject("kiosk_mode") ?: JSONObject()
        
        // Screen always on setting
        if (kioskMode.optBoolean("keep_screen_on", true)) {
            window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        }
        
        // Immersive mode
        if (config.optBoolean("immersive_mode", true)) {
            WindowCompat.setDecorFitsSystemWindows(window, false)
            applyImmersiveSticky()
        }
        
        // Haptic feedback setting
        webView.isHapticFeedbackEnabled = config.optBoolean("haptic_feedback", false)
    }

    /**
     * Configure WebView settings based on configuration
     */
    private fun configureWebView() {
        webView.settings.apply {
            javaScriptEnabled = config.optBoolean("javascript_enabled", true)
            
            // Cache mode handling
            when (config.optString("cache_mode", "no_cache")) {
                "no_cache" -> cacheMode = WebSettings.LOAD_NO_CACHE
                "default" -> cacheMode = WebSettings.LOAD_DEFAULT
                "cache_else_network" -> cacheMode = WebSettings.LOAD_CACHE_ELSE_NETWORK
                "cache_first" -> cacheMode = WebSettings.LOAD_CACHE_FIRST
                else -> cacheMode = WebSettings.LOAD_NO_CACHE
            }
            
            @Suppress("DEPRECATION") setAppCacheEnabled(false)
            domStorageEnabled = config.optBoolean("dom_storage_enabled", true)
            setSupportZoom(config.optBoolean("zoom_enabled", false))
        }
        webView.clearCache(true)

        // Custom WebViewClient for security features
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, url: String?): Boolean {
                url?.let { url ->
                    // Check URL whitelist if configured
                    val security = config.optJSONObject("security")
                    val allowedHosts = security?.optJSONArray("allowed_hosts")
                    if (allowedHosts?.length() ?: 0 > 0) {
                        val uri = android.net.Uri.parse(url)
                        val host = uri.host
                        var hostAllowed = false
                        for (i in 0 until allowedHosts.length()) {
                            if (allowedHosts.getString(i) == host) {
                                hostAllowed = true
                                break
                            }
                        }
                        if (!hostAllowed) return true // Block navigation
                    }
                    
                    // Block external links if configured
                    if (security?.optBoolean("block_external_links", true) == true && 
                        !url.startsWith("https://www.napolyane.com")) {
                        return true // Block navigation
                    }
                }
                return false // Allow navigation in WebView
            }
        }

        // Kiosk hardening: disable long-press context menu
        webView.isLongClickable = false
        webView.setOnLongClickListener { true }
        
        // Reset idle timeout on user interaction
        setupUserInteractionListener()
    }

    /**
     * Set up touch listener to reset idle timeout on user interaction
     */
    private fun setupUserInteractionListener() {
        webView.setOnTouchListener { _, event ->
            resetIdleTimeout()
            false // Continue normal touch processing
        }
    }

    override fun onResume() {
        super.onResume()
        if (config.optBoolean("immersive_mode", true)) {
            applyImmersiveSticky()
        }
        resetIdleTimeout()
    }

    override fun onPause() {
        super.onPause()
        idleTimeoutRunnable?.let { handler.removeCallbacks(it) }
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus && config.optBoolean("immersive_mode", true)) {
            applyImmersiveSticky()
        }
    }

    @Deprecated("Kiosk mode: back navigation is intentionally disabled")
    override fun onBackPressed() {
        val kioskMode = config.optJSONObject("kiosk_mode") ?: JSONObject()
        // In kiosk mode we intentionally ignore BACK so the user can't leave the web experience.
        if (kioskMode.optBoolean("disable_back_button", true)) {
            // Do nothing - back button is disabled in kiosk mode
            return
        }
        super.onBackPressed()
    }

    override fun dispatchKeyEvent(event: KeyEvent): Boolean {
        val kioskMode = config.optJSONObject("kiosk_mode") ?: JSONObject()
        
        // Best-effort kiosk protection: consume keys that would let the user exit/switch apps.
        // (HOME is not always delivered to apps, but consuming it when delivered avoids leaks.)
        when (event.keyCode) {
            KeyEvent.KEYCODE_BACK -> {
                if (kioskMode.optBoolean("disable_back_button", true)) {
                    resetIdleTimeout()
                    return true
                }
            }
            KeyEvent.KEYCODE_HOME -> {
                if (kioskMode.optBoolean("disable_home_button", true)) {
                    resetIdleTimeout()
                    return true
                }
            }
            KeyEvent.KEYCODE_APP_SWITCH -> {
                if (kioskMode.optBoolean("disable_app_switch", true)) {
                    resetIdleTimeout()
                    return true
                }
            }
        }
        return super.dispatchKeyEvent(event)
    }

    /**
     * Apply immersive sticky mode to hide system bars
     */
    private fun applyImmersiveSticky() {
        WindowInsetsControllerCompat(window, webView).apply {
            hide(WindowInsetsCompat.Type.systemBars())
            systemBarsBehavior =
                WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        }
    }

    /**
     * Reset the idle timeout countdown based on configuration
     */
    private fun resetIdleTimeout() {
        idleTimeoutRunnable?.let { handler.removeCallbacks(it) }
        
        val idleTimeoutMs = config.optLong("idle_timeout_ms", 300000)
        if (idleTimeoutMs > 0) {
            idleTimeoutRunnable = Runnable {
                restartKiosk()
            }
            idleTimeoutRunnable?.let {
                handler.postDelayed(it, idleTimeoutMs)
            }
        }
    }

    /**
     * Restart the kiosk application when idle timeout is reached
     */
    private fun restartKiosk() {
        // Clear WebView cache and data
        webView.clearCache(true)
        webView.clearHistory()
        webView.clearFormData()
        
        // Reload the configured URL
        webView.loadUrl(config.optString("url", ""))
        
        // Reset idle timeout
        resetIdleTimeout()
    }
}
