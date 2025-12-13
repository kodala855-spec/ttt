package com.napolyane.kiosk

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Color
import android.net.ConnectivityManager
import android.net.Uri
import android.os.Bundle
import android.os.SystemClock
import android.text.InputType
import android.view.View
import android.view.WindowManager
import android.webkit.DownloadListener
import android.webkit.SslErrorHandler
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.net.http.SslError
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import org.json.JSONObject

class KioskActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var errorOverlay: View
    private lateinit var errorMessage: TextView
    private lateinit var retryButton: Button
    private lateinit var devHotspot: View

    private lateinit var config: KioskConfig

    private var hadLoadError: Boolean = false

    private var tapCount = 0
    private var firstTapAtMs = 0L

    private val connectivityManager by lazy {
        getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
    }

    private val networkCallback = object : ConnectivityManager.NetworkCallback() {
        override fun onAvailable(network: android.net.Network) {
            if (hadLoadError) {
                webView.post {
                    hideLoadError()
                    webView.reload()
                }
            }
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        WindowCompat.setDecorFitsSystemWindows(window, false)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        setContentView(R.layout.activity_kiosk)

        config = KioskConfig.load(this)

        webView = findViewById(R.id.webView)
        errorOverlay = findViewById(R.id.errorOverlay)
        errorMessage = findViewById(R.id.errorMessage)
        retryButton = findViewById(R.id.retryButton)
        devHotspot = findViewById(R.id.devHotspot)

        retryButton.setOnClickListener {
            hideLoadError()
            webView.reload()
        }

        devHotspot.setOnClickListener { onDeveloperHotspotTapped() }

        configureWebView()

        if (savedInstanceState == null) {
            webView.loadUrl(config.startUrl)
        }
    }

    override fun onStart() {
        super.onStart()
        try {
            connectivityManager.registerDefaultNetworkCallback(networkCallback)
        } catch (_: Exception) {
        }
    }

    override fun onStop() {
        try {
            connectivityManager.unregisterNetworkCallback(networkCallback)
        } catch (_: Exception) {
        }
        super.onStop()
    }

    override fun onResume() {
        super.onResume()
        applyImmersiveMode()
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) {
            applyImmersiveMode()
        }
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            val backForwardList = webView.copyBackForwardList()
            val targetIndex = backForwardList.currentIndex - 1
            val targetUrl = if (targetIndex >= 0) backForwardList.getItemAtIndex(targetIndex).url else null

            if (targetUrl != null && isAllowedNavigation(Uri.parse(targetUrl))) {
                webView.goBack()
                return
            }
        }
    }

    private fun applyImmersiveMode() {
        val controller = WindowInsetsControllerCompat(window, window.decorView)
        controller.hide(WindowInsetsCompat.Type.systemBars())
        controller.systemBarsBehavior =
            WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
    }

    private fun configureWebView() {
        webView.setBackgroundColor(Color.BLACK)

        webView.setOnLongClickListener { true }
        webView.isLongClickable = false
        webView.isHapticFeedbackEnabled = false

        val settings = webView.settings
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.cacheMode = WebSettings.LOAD_NO_CACHE
        @Suppress("DEPRECATION")
        settings.setAppCacheEnabled(false)
        settings.setSupportZoom(false)
        settings.builtInZoomControls = false
        settings.displayZoomControls = false
        settings.useWideViewPort = true
        settings.loadWithOverviewMode = true
        settings.setSupportMultipleWindows(false)
        settings.javaScriptCanOpenWindowsAutomatically = false
        settings.mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
        settings.allowFileAccess = false
        settings.allowContentAccess = false

        webView.webChromeClient = object : WebChromeClient() {
            override fun onCreateWindow(
                view: WebView,
                isDialog: Boolean,
                isUserGesture: Boolean,
                resultMsg: android.os.Message
            ): Boolean {
                return false
            }

            override fun onShowFileChooser(
                webView: WebView,
                filePathCallback: android.webkit.ValueCallback<Array<Uri>>,
                fileChooserParams: FileChooserParams
            ): Boolean {
                filePathCallback.onReceiveValue(null)
                return true
            }
        }

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val url = request.url
                if (!isAllowedNavigation(url)) {
                    return true
                }
                return false
            }

            @Deprecated("Deprecated in Java")
            override fun shouldOverrideUrlLoading(view: WebView, url: String): Boolean {
                val uri = Uri.parse(url)
                return !isAllowedNavigation(uri)
            }

            override fun onReceivedError(
                view: WebView,
                request: WebResourceRequest,
                error: WebResourceError
            ) {
                if (request.isForMainFrame) {
                    showLoadError("Unable to load. Check connection.")
                }
            }

            @Deprecated("Deprecated in Java")
            override fun onReceivedError(
                view: WebView,
                errorCode: Int,
                description: String,
                failingUrl: String
            ) {
                showLoadError("Unable to load. Check connection.")
            }

            override fun onReceivedSslError(
                view: WebView,
                handler: SslErrorHandler,
                error: SslError
            ) {
                handler.cancel()
                showLoadError("Secure connection error.")
            }

            override fun onPageFinished(view: WebView, url: String) {
                hadLoadError = false
                hideLoadError()
                super.onPageFinished(view, url)
            }
        }

        webView.setDownloadListener(DownloadListener { _, _, _, _, _ ->
        })
    }

    private fun isAllowedNavigation(uri: Uri): Boolean {
        val scheme = uri.scheme?.lowercase() ?: return false
        if (scheme != "https" && scheme != "http") {
            return false
        }

        val host = uri.host ?: return false
        return host.equals(config.allowedHost, ignoreCase = true)
    }

    private fun showLoadError(message: String) {
        hadLoadError = true
        errorMessage.text = message
        errorOverlay.visibility = View.VISIBLE
    }

    private fun hideLoadError() {
        errorOverlay.visibility = View.GONE
    }

    private fun onDeveloperHotspotTapped() {
        val now = SystemClock.elapsedRealtime()

        if (tapCount == 0 || now - firstTapAtMs > DEV_TAP_WINDOW_MS) {
            tapCount = 0
            firstTapAtMs = now
        }

        tapCount++

        if (tapCount >= DEV_TAP_COUNT) {
            tapCount = 0
            showExitDialog()
        }
    }

    private fun showExitDialog() {
        val input = EditText(this).apply {
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD
        }

        val dialog = AlertDialog.Builder(this)
            .setTitle("Service")
            .setMessage("Enter service code")
            .setView(input)
            .setPositiveButton("Exit", null)
            .setNegativeButton("Cancel", null)
            .create()

        dialog.setOnShowListener {
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener {
                val entered = input.text?.toString().orEmpty()
                if (entered == config.exitCode) {
                    exitForService()
                    dialog.dismiss()
                } else {
                    input.error = "Incorrect code"
                }
            }
        }

        dialog.show()
    }

    private fun exitForService() {
        try {
            stopLockTask()
        } catch (_: Exception) {
        }
        finishAndRemoveTask()
    }

    private data class KioskConfig(
        val startUrl: String,
        val allowedHost: String,
        val exitCode: String
    ) {
        companion object {
            fun load(context: Context): KioskConfig {
                val jsonText = context.assets.open("kiosk_config.json")
                    .bufferedReader()
                    .use { it.readText() }

                val json = JSONObject(jsonText)
                val startUrl = json.getString("startUrl")
                val allowedHost = json.getString("allowedHost")
                val exitCode = json.getString("exitCode")

                return KioskConfig(
                    startUrl = startUrl,
                    allowedHost = allowedHost,
                    exitCode = exitCode
                )
            }
        }
    }

    private companion object {
        private const val DEV_TAP_COUNT = 5
        private const val DEV_TAP_WINDOW_MS = 2500L
    }
}
