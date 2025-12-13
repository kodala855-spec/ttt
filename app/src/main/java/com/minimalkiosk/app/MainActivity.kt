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
import org.json.JSONObject

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        webView = WebView(this).apply {
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
        }
        setContentView(webView)

        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        WindowCompat.setDecorFitsSystemWindows(window, false)
        applyImmersiveSticky()

        webView.settings.apply {
            javaScriptEnabled = true
            cacheMode = WebSettings.LOAD_NO_CACHE
            @Suppress("DEPRECATION") setAppCacheEnabled(false)
            domStorageEnabled = true
            setSupportZoom(false)
        }
        webView.clearCache(true)

        // Ensure links stay inside this WebView (default behavior only applies when a WebViewClient is set).
        webView.webViewClient = object : WebViewClient() {}

        // Kiosk hardening: disable long-press so the user can't open the WebView context menu
        // (copy/paste, open-in-new-tab, etc.) and escape the kiosk flow.
        webView.isHapticFeedbackEnabled = false
        webView.isLongClickable = false
        webView.setOnLongClickListener { true }

        webView.loadUrl(readTargetUrl())
    }

    override fun onResume() {
        super.onResume()
        applyImmersiveSticky()
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) applyImmersiveSticky()
    }

    @Deprecated("Kiosk mode: back navigation is intentionally disabled")
    override fun onBackPressed() {
        // In kiosk mode we intentionally ignore BACK so the user can't leave the web experience.
    }

    override fun dispatchKeyEvent(event: KeyEvent): Boolean {
        // Best-effort kiosk protection: consume keys that would let the user exit/switch apps.
        // (HOME is not always delivered to apps, but consuming it when delivered avoids leaks.)
        when (event.keyCode) {
            KeyEvent.KEYCODE_BACK,
            KeyEvent.KEYCODE_HOME,
            KeyEvent.KEYCODE_APP_SWITCH -> return true
        }
        return super.dispatchKeyEvent(event)
    }

    private fun applyImmersiveSticky() {
        WindowInsetsControllerCompat(window, webView).apply {
            hide(WindowInsetsCompat.Type.systemBars())
            systemBarsBehavior =
                WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        }
    }

    private fun readTargetUrl(): String {
        val fallback = "https://www.napolyane.com/menu-restaurant"
        return runCatching {
            val raw = assets.open("kiosk_config.json").bufferedReader().use { it.readText() }
            JSONObject(raw).optString("url").takeIf { it.isNotBlank() } ?: fallback
        }.getOrDefault(fallback)
    }
}
