package com.example.kiosk;

import android.app.Activity;
import android.graphics.Bitmap;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import org.json.JSONObject;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public class MainActivity extends Activity {

    private WebView webView;
    private LinearLayout errorLayout;
    private String startUrl;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        setImmersiveMode();

        webView = findViewById(R.id.webview);
        errorLayout = findViewById(R.id.error_layout);
        Button retryButton = findViewById(R.id.retry_button);

        setupWebView();

        startUrl = loadUrlFromConfig();
        webView.loadUrl(startUrl);

        retryButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                errorLayout.setVisibility(View.GONE);
                webView.reload();
            }
        });
    }

    private void setupWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                // Keep navigation inside the app
                return false;
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                 if (request.isForMainFrame()) {
                     errorLayout.setVisibility(View.VISIBLE);
                 }
            }

             @Override
             public void onPageStarted(WebView view, String url, Bitmap favicon) {
                 errorLayout.setVisibility(View.GONE);
             }
        });
    }

    private String loadUrlFromConfig() {
        String defaultUrl = "https://www.napolyane.com/menu-restaurant";
        try {
            InputStream is = getAssets().open("config.json");
            int size = is.available();
            byte[] buffer = new byte[size];
            is.read(buffer);
            is.close();
            String json = new String(buffer, StandardCharsets.UTF_8);
            JSONObject jsonObject = new JSONObject(json);
            return jsonObject.optString("url", defaultUrl);
        } catch (Exception e) {
            return defaultUrl;
        }
    }

    @Override
    public void onBackPressed() {
        // No-op to disable back navigation
    }
    
    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) {
            setImmersiveMode();
        }
    }

    private void setImmersiveMode() {
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
    }
}
