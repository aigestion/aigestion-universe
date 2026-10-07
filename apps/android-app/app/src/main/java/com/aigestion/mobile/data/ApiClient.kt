package com.aigestion.mobile.data

import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.get
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.contentType
import io.ktor.serialization.kotlinx.json.json
import kotlinx.serialization.json.Json

object ApiClient {
    private const val BASE_URL = "http://10.0.2.2:9200" // Android emulator -> host

    val client: HttpClient = HttpClient {
        install(ContentNegotiation) {
            json(Json { ignoreUnknownKeys = true; prettyPrint = true })
        }
    }

    suspend inline fun <reified T> get(path: String): T =
        client.get(BASE_URL + path).body()

    suspend inline fun <reified T> post(path: String, body: Any): T =
        client.post(BASE_URL + path) {
            contentType(ContentType.Application.Json)
            setBody(body)
        }.body()
}

@kotlinx.serialization.Serializable
data class BrainStats(
    val coherence_level: Int = 4,
    val empathy_base: Double = 0.96,
    val max_nodes: Int = 12480,
    val nodes: Int = 0,
)

@kotlinx.serialization.Serializable
data class EngineInfo(
    val engine: String,
    val endpoint: String,
    val healthy: Boolean = true,
    val load: Double = 0.0,
)

@kotlinx.serialization.Serializable
data class EngineList(val engines: List<EngineInfo> = emptyList())

@kotlinx.serialization.Serializable
data class MemoryStats(val tiers: Map<String, Int> = emptyMap())
