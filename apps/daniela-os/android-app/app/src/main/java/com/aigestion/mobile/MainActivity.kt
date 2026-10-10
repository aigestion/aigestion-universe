package com.aigestion.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.aigestion.mobile.data.SettingsRepository
import com.aigestion.mobile.ui.AppState
import com.aigestion.mobile.ui.AppViewModel
import com.aigestion.mobile.ui.ConnState

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // La URL ya no vive en la Activity: se inyecta vía BuildConfig y se
        // persiste en SharedPreferences (ver data/SettingsRepository.kt).
        val settings = SettingsRepository(this)

        setContent {
            AIGestionTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background,
                ) {
                    AIGestionApp(
                        settings = settings,
                        viewModel = viewModel(
                            factory = AppViewModel.factory(settings),
                        ),
                    )
                }
            }
        }
    }
}

@Composable
fun AIGestionTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = darkColorScheme(), content = content)
}

private val QUICK_COMMANDS = listOf("estado", "ayuda", "hola", "qué puedes hacer")

@Composable
fun AIGestionApp(
    settings: SettingsRepository,
    viewModel: AppViewModel,
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val listState = rememberLazyListState()
    var showUrlEditor by rememberSaveable { mutableStateOf(false) }

    // Auto-scroll al último mensaje (tu `items` de LazyColumn no tenía key).
    LaunchedEffect(state.messages.size) {
        if (state.messages.isNotEmpty()) {
            listState.animateScrollToItem(state.messages.size - 1)
        }
    }

    Scaffold { inner ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(inner)
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text(
                text = "aigestion.net",
                style = MaterialTheme.typography.headlineMedium,
            )
            Text(
                text = state.url,
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            Spacer(Modifier.height(8.dp))

            ConnectionCard(state) { showUrlEditor = true }

            Spacer(Modifier.height(16.dp))

            Conversation(
                state = state,
                listState = listState,
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
            )

            Spacer(Modifier.height(8.dp))

            OutlinedTextField(
                value = state.draft,
                onValueChange = viewModel::onDraftChange,
                label = { Text("Escribe un comando…") },
                modifier = Modifier.fillMaxWidth(),
                enabled = !state.pending,
                singleLine = false,
                maxLines = 3,
            )

            Spacer(Modifier.height(8.dp))

            Button(
                onClick = { viewModel.send() },
                enabled = state.canSend,
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (state.pending) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(18.dp),
                        strokeWidth = 2.dp,
                    )
                } else {
                    Text("Enviar")
                }
            }

            Spacer(Modifier.height(16.dp))

            Text(
                text = "Acciones rápidas:",
                style = MaterialTheme.typography.titleSmall,
            )
            Spacer(Modifier.height(8.dp))

            LazyColumn(
                modifier = Modifier.height(140.dp),
                verticalArrangement = Arrangement.spacedBy(4.dp),
            ) {
                items(QUICK_COMMANDS) { comando ->
                    OutlinedButton(
                        onClick = { viewModel.send(comando) },
                        modifier = Modifier.fillMaxWidth(),
                        enabled = state.conn == ConnState.OK && !state.pending,
                    ) {
                        Text(comando)
                    }
                }
            }

            Row(horizontalArrangement = Arrangement.End, modifier = Modifier.fillMaxWidth()) {
                if (state.messages.isNotEmpty()) {
                    TextButton(onClick = viewModel::clearMessages) { Text("Limpiar") }
                }
                TextButton(onClick = viewModel::refresh) { Text("Reintentar") }
            }
        }
    }

    if (showUrlEditor) {
        UrlEditorDialog(
            initial = settings.baseUrl,
            onDismiss = { showUrlEditor = false },
            onSave = { value ->
                viewModel.setBaseUrl(value)
                showUrlEditor = false
            },
        )
    }
}

@Composable
private fun ConnectionCard(state: AppState, onClick: () -> Unit) {
    val (bg, label) = when (state.conn) {
        ConnState.OK ->
            MaterialTheme.colorScheme.primaryContainer to "✅ Conectado al PC"
        ConnState.CHECKING ->
            MaterialTheme.colorScheme.surfaceVariant to "⏳ Comprobando…"
        ConnState.OFFLINE ->
            MaterialTheme.colorScheme.errorContainer to "❌ Sin conexión"
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = bg),
    ) {
        Column(Modifier.padding(16.dp)) {
            Text(label, modifier = Modifier.fillMaxWidth())
            if (state.connDetail.isNotBlank()) {
                Text(
                    text = state.connDetail,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            TextButton(onClick = onClick) { Text("Cambiar URL") }
        }
    }
}

@Composable
private fun Conversation(
    state: AppState,
    listState: LazyListState,
    modifier: Modifier = Modifier,
) {
    if (state.messages.isEmpty()) {
        Column(
            modifier = modifier,
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text(
                text = "Aún no hay mensajes. Prueba «hola».",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        return
    }

    LazyColumn(
        state = listState,
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(6.dp),
        contentPadding = PaddingValues(vertical = 4.dp),
    ) {
        items(state.messages, key = { it.id }) { msg ->
            Column(
                modifier = Modifier.fillMaxWidth(),
                horizontalAlignment = if (msg.mine) Alignment.End else Alignment.Start,
            ) {
                Surface(
                    color = when {
                        msg.failed -> MaterialTheme.colorScheme.errorContainer
                        msg.mine -> MaterialTheme.colorScheme.primaryContainer
                        else -> MaterialTheme.colorScheme.surfaceVariant
                    },
                    shape = MaterialTheme.shapes.medium,
                ) {
                    Text(
                        text = msg.text,
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
                Spacer(Modifier.height(2.dp))
            }
        }
    }
}

@Composable
private fun UrlEditorDialog(
    initial: String,
    onDismiss: () -> Unit,
    onSave: (String) -> Unit,
) {
    var value by remember { mutableStateOf(initial) }

    Dialog(onDismissRequest = onDismiss) {
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(Modifier.padding(20.dp)) {
                Text(
                    "URL del backend",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                )
                Spacer(Modifier.height(12.dp))
                OutlinedTextField(
                    value = value,
                    onValueChange = { value = it },
                    label = { Text("http://192.168.x.x:5000") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                Spacer(Modifier.height(16.dp))
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.End,
                ) {
                    TextButton(onClick = onDismiss) { Text("Cancelar") }
                    Spacer(Modifier.width(8.dp))
                    Button(
                        onClick = { onSave(value) },
                        enabled = value.isNotBlank(),
                    ) { Text("Guardar") }
                }
            }
        }
    }
}
