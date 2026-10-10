package com.aigestion.mobile.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.CreationExtras
import com.aigestion.mobile.data.ChatApi
import com.aigestion.mobile.data.ChatResult
import com.aigestion.mobile.data.SettingsRepository
import com.aigestion.mobile.data.StatusResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

enum class ConnState { CHECKING, OK, OFFLINE }

data class Message(
    val id: Long,
    val text: String,
    val mine: Boolean,
    val failed: Boolean = false,
)

data class AppState(
    val url: String = "",
    val conn: ConnState = ConnState.CHECKING,
    val connDetail: String = "",
    val coreStatus: String = "",
    val messages: List<Message> = emptyList(),
    val pending: Boolean = false,
    val draft: String = "",
) {
    val canSend: Boolean get() = draft.isNotBlank() && !pending
}

/**
 * Estado de la app en un único [StateFlow].
 *
 * Motivo del refactor: sin ViewModel, rotar la pantalla recreaba la Activity
 * y perdía `mensaje`, `respuesta` e `isConnected`, además de seguir pendiente
 * una coroutine ya huerfana que escribía sobre `remember` viejos.
 */
class AppViewModel(
    private val api: ChatApi,
    private val settings: SettingsRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(AppState(url = settings.baseUrl))
    val state: StateFlow<AppState> = _state.asStateFlow()

    private var nextId = 0L

    init {
        refresh()
    }

    /** Reconsulta `GET /api/status`. */
    fun refresh() {
        val snapshot = _state.value
        _state.value = snapshot.copy(conn = ConnState.CHECKING, connDetail = "")
        viewModelScope.launch {
            when (val r = api.status()) {
                is StatusResult.Reachable -> _state.value = _state.value.copy(
                    conn = ConnState.OK,
                    connDetail = "v${r.version} · core ${r.coreStatus}",
                    coreStatus = r.coreStatus,
                )
                is StatusResult.Unreachable -> _state.value = _state.value.copy(
                    conn = ConnState.OFFLINE,
                    connDetail = r.reason,
                    coreStatus = "",
                )
            }
        }
    }

    fun onDraftChange(value: String) {
        _state.value = _state.value.copy(draft = value)
    }

    /** Envía el borrador actual y añade la respuesta al hilo. */
    fun send() {
        send(_state.value.draft)
    }

    /** Envía un comando fijo (botones de acciones rápidas). */
    fun send(command: String) {
        val text = command.trim()
        if (text.isEmpty() || _state.value.pending) return

        push(text, mine = true)
        _state.value = _state.value.copy(draft = "", pending = true)

        viewModelScope.launch {
            when (val r = api.chat(text)) {
                is ChatResult.Ok -> {
                    push(r.response, mine = false)
                    _state.value = _state.value.copy(pending = false, conn = ConnState.OK)
                }
                is ChatResult.Error -> {
                    push("⚠ ${r.message}", mine = false, failed = true)
                    _state.value = _state.value.copy(pending = false, conn = ConnState.OFFLINE)
                }
            }
        }
    }

    /** Cambia la URL del backend y la sondea. */
    fun setBaseUrl(raw: String) {
        settings.baseUrl = raw
        refresh()
        _state.value = _state.value.copy(url = settings.baseUrl)
    }

    fun clearMessages() {
        _state.value = _state.value.copy(messages = emptyList())
    }

    private fun push(text: String, mine: Boolean, failed: Boolean = false) {
        val message = Message(id = nextId++, text = text, mine = mine, failed = failed)
        _state.value = _state.value.copy(messages = _state.value.messages + message)
    }

    companion object {
        fun factory(settings: SettingsRepository): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {

                /** Las dos firmas se implementan a propósito: en lifecycle 2.x una de
                 *  ellas puede seguir siendo abstracta y no implementarla rompe la
                 *  compilación, sin ninguna ventaja. */
                override fun <T : ViewModel> create(modelClass: Class<T>): T = createInternal(modelClass)

                override fun <T : ViewModel> create(
                    modelClass: Class<T>,
                    extras: CreationExtras,
                ): T = createInternal(modelClass)

                private fun <T : ViewModel> createInternal(modelClass: Class<T>): T {
                    check(modelClass.isAssignableFrom(AppViewModel::class.java)) {
                        "ViewModel desconocida: $modelClass"
                    }
                    @Suppress("UNCHECKED_CAST")
                    return AppViewModel(ChatApi { settings.baseUrl }, settings) as T
                }
            }
    }
}
