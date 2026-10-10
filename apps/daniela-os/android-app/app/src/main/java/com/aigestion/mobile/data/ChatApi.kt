package com.aigestion.mobile.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/** Resultado de `POST /api/chat`. */
sealed interface ChatResult {
    data class Ok(val response: String) : ChatResult
    data class Error(val message: String) : ChatResult
}

/** Resultado de `GET /api/status`. */
sealed interface StatusResult {
    data class Reachable(val version: String, val coreStatus: String) : StatusResult
    data class Unreachable(val reason: String) : StatusResult
}

/**
 * Cliente HTTP mínimo contra el backend de Daniela OS.
 *
 * @param baseUrlProvider lambda que devuelve la URL base actual
 *   (p. ej. `http://192.168.1.170:5000`), para que los cambios
 *   en [SettingsRepository.baseUrl] se reflejen sin recrear el cliente.
 */
class ChatApi(
    private val baseUrlProvider: () -> String,
) {
    /** `GET /api/status` → estado del backend y del core. */
    suspend fun status(): StatusResult = withContext(Dispatchers.IO) {
        try {
            val base = baseUrlProvider().trimEnd('/')
            val conn = (URL("$base/api/status").openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = 8000
                readTimeout = 8000
            }
            val code = conn.responseCode
            if (code != HttpURLConnection.HTTP_OK) {
                return@withContext StatusResult.Unreachable("HTTP $code")
            }
            val body = conn.inputStream.bufferedReader().use { it.readText() }
            val json = JSONObject(body)
            StatusResult.Reachable(
                version = json.optString("version", "?"),
                coreStatus = json.optString("core_status", json.optString("coreStatus", "?")),
            )
        } catch (e: Exception) {
            StatusResult.Unreachable(e.message ?: e.javaClass.simpleName)
        }
    }

    /** `POST /api/chat` con `{"message": ...}` → texto de respuesta. */
    suspend fun chat(text: String): ChatResult = withContext(Dispatchers.IO) {
        try {
            val base = baseUrlProvider().trimEnd('/')
            val conn = (URL("$base/api/chat").openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                doOutput = true
                connectTimeout = 15000
                readTimeout = 60000
                setRequestProperty("Content-Type", "application/json")
            }
            val payload = JSONObject().put("message", text).toString()
            conn.outputStream.bufferedWriter().use { it.write(payload) }
            val code = conn.responseCode
            val stream = if (code == HttpURLConnection.HTTP_OK) conn.inputStream else conn.errorStream
            val body = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
            if (code != HttpURLConnection.HTTP_OK) {
                return@withContext ChatResult.Error("HTTP $code: ${body.take(200)}")
            }
            val json = JSONObject(body)
            ChatResult.Ok(json.optString("response", body))
        } catch (e: Exception) {
            ChatResult.Error(e.message ?: e.javaClass.simpleName)
        }
    }
}
