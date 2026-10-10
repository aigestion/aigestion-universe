package com.aigestion.mobile.data

import android.content.Context
import android.content.SharedPreferences
import androidx.core.content.edit
import com.aigestion.mobile.BuildConfig

/**
 * URL base del backend, persistida en [SharedPreferences].
 *
 * Orden de resolución (igual que el README):
 * 1. Valor guardado por el usuario (diálogo *Cambiar URL*).
 * 2. `BuildConfig.API_BASE_URL` (fijada con `-PapiBaseUrl=...`).
 * 3. Valor por defecto `http://192.168.1.170:5000`.
 */
class SettingsRepository(context: Context) {

    private val prefs: SharedPreferences =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    var baseUrl: String
        get() = prefs.getString(KEY_BASE_URL, null)
            ?: BuildConfig.API_BASE_URL.ifBlank { DEFAULT_BASE_URL }
        set(value) {
            prefs.edit { putString(KEY_BASE_URL, value.trim()) }
        }

    companion object {
        private const val PREFS_NAME = "daniela_settings"
        private const val KEY_BASE_URL = "api_base_url"
        const val DEFAULT_BASE_URL = "http://192.168.1.170:5000"
    }
}
