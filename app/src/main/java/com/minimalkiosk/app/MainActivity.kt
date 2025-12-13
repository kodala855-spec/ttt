package com.minimalkiosk.app

import android.app.ActivityManager
import android.app.AlertDialog
import android.graphics.PixelFormat
import android.os.Bundle
import android.text.InputType
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.EditText
import android.widget.LinearLayout
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    private var tapCount = 0
    private var lastTapTime = 0L
    private val TAP_TIMEOUT = 3000L // 3 seconds window
    private val EXIT_PIN = "1234"
    private var overlayView: View? = null
    private var windowManager: WindowManager? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // Enable LockTask mode
        try {
            val am = getSystemService(ACTIVITY_SERVICE) as ActivityManager
            am.lockTaskModeState // Request LockTask mode
            startLockTask()
        } catch (e: Exception) {
            e.printStackTrace()
        }
        
        // Create invisible tap overlay in top-left corner
        createExitOverlay()
    }

    private fun createExitOverlay() {
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        
        // Create invisible overlay view in top-left corner
        overlayView = View(this).apply {
            setOnTouchListener { _, event ->
                if (event.action == MotionEvent.ACTION_UP) {
                    handleExitTap()
                }
                true
            }
        }
        
        val params = WindowManager.LayoutParams().apply {
            type = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
            format = PixelFormat.TRANSPARENT
            flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
            width = 150
            height = 150
            x = 0
            y = 0
            gravity = Gravity.TOP or Gravity.START
        }
        
        try {
            windowManager?.addView(overlayView, params)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun handleExitTap() {
        val currentTime = System.currentTimeMillis()
        
        // Reset if timeout exceeded
        if (currentTime - lastTapTime > TAP_TIMEOUT) {
            tapCount = 0
        }
        
        tapCount++
        lastTapTime = currentTime
        
        // Check if 5 taps detected within time window
        if (tapCount >= 5) {
            tapCount = 0
            showPinDialog()
        }
    }

    private fun showPinDialog() {
        val editText = EditText(this).apply {
            inputType = InputType.TYPE_CLASS_NUMBER or InputType.TYPE_NUMBER_VARIATION_PASSWORD
            hint = "Enter PIN"
        }
        
        val container = LinearLayout(this).apply {
            addView(editText, LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                setMargins(48, 0, 48, 0)
            })
        }
        
        AlertDialog.Builder(this)
            .setTitle("Developer Exit")
            .setView(container)
            .setPositiveButton("OK") { _, _ ->
                if (editText.text.toString() == EXIT_PIN) {
                    exitKioskMode()
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun exitKioskMode() {
        try {
            stopLockTask()
        } catch (e: Exception) {
            e.printStackTrace()
        }
        
        // Remove overlay
        try {
            overlayView?.let { windowManager?.removeView(it) }
        } catch (e: Exception) {
            e.printStackTrace()
        }
        
        finish()
    }

    override fun onDestroy() {
        super.onDestroy()
        try {
            overlayView?.let { windowManager?.removeView(it) }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
}