package com.example.kiosk

import android.os.Bundle
import android.util.Log
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class KioskActivity : AppCompatActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_kiosk)
        
        // Load and parse config
        val config = KioskConfig.fromAssets(this)
        
        // Display the config info for verification
        val configText = """
            Kiosk Configuration:
            Menu URL: ${config.menuUrl}
            Developer Code: ${config.developerCode}
            Version: ${BuildConfig.VERSION_NAME}
        """.trimIndent()
        
        findViewById<TextView>(R.id.configText)?.text = configText
        
        Log.i("KioskActivity", "Kiosk config loaded successfully")
        Log.i("KioskActivity", "Menu URL: ${config.menuUrl}")
        Log.i("KioskActivity", "Developer Code: ${config.developerCode}")
    }
}