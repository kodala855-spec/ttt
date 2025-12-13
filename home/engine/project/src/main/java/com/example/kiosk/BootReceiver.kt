package com.example.kiosk

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import android.widget.Toast

class BootReceiver : BroadcastReceiver() {
    
    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action
        
        when (action) {
            Intent.ACTION_BOOT_COMPLETED, Intent.ACTION_LOCKED_BOOT_COMPLETED -> {
                if (hasValidKioskConfig(context)) {
                    startMainActivity(context)
                    showBootMessage(context)
                    Log.i(TAG, "Boot receiver triggered for action: $action")
                }
            }
        }
    }
    
    private fun hasValidKioskConfig(context: Context): Boolean {
        val prefs = context.getSharedPreferences(KIOSK_PREFS, Context.MODE_PRIVATE)
        return prefs.getBoolean(KEY_KIOSK_ENABLED, false)
    }
    
    private fun startMainActivity(context: Context) {
        val mainIntent = Intent(context, MainActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        context.startActivity(mainIntent)
    }
    
    private fun showBootMessage(context: Context) {
        Toast.makeText(context, "Kiosk app starting...", Toast.LENGTH_SHORT).show()
    }
    
    companion object {
        private const val TAG = "BootReceiver"
        private const val KIOSK_PREFS = "kiosk_prefs"
        private const val KEY_KIOSK_ENABLED = "kiosk_enabled"
    }
}