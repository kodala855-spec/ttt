package com.example.kiosk

import android.content.Context
import org.json.JSONObject
import java.io.IOException

data class KioskConfig(
    val menuUrl: String,
    val developerCode: String
) {
    companion object {
        fun fromAssets(context: Context): KioskConfig {
            return try {
                val inputStream = context.assets.open("kiosk_config.json")
                val size = inputStream.available()
                val buffer = ByteArray(size)
                inputStream.read(buffer)
                inputStream.close()
                val jsonString = String(buffer, Charsets.UTF_8)
                
                val jsonObject = JSONObject(jsonString)
                KioskConfig(
                    menuUrl = jsonObject.getString("menuUrl"),
                    developerCode = jsonObject.getString("developerCode")
                )
            } catch (e: IOException) {
                // Return default config if file cannot be read
                KioskConfig(
                    menuUrl = "https://www.napolyane.com/menu-restaurant",
                    developerCode = "1234"
                )
            } catch (e: Exception) {
                // Return default config if JSON parsing fails
                KioskConfig(
                    menuUrl = "https://www.napolyane.com/menu-restaurant",
                    developerCode = "1234"
                )
            }
        }
    }
}