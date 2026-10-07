package com.aigestion.mobile.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aigestion.mobile.data.EngineInfo
import com.aigestion.mobile.ui.theme.NeuralCyan
import com.aigestion.mobile.ui.theme.NeuralGreen
import com.aigestion.mobile.ui.theme.NeuralMuted
import com.aigestion.mobile.ui.theme.NeuralRed

@Composable
fun EnginesScreen(innerPadding: PaddingValues) {
    val engines = remember {
        listOf(
            EngineInfo("core", "daniela:9200", true, 0.12f),
            EngineInfo("secure", "security:9999", true, 0.08f),
            EngineInfo("performance", "perf:9998", true, 0.21f),
            EngineInfo("automation", "auto:9900", true, 0.05f),
            EngineInfo("agent_mobile", "mobile:9800", true, 0.15f),
        )
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(innerPadding)
            .padding(16.dp)
    ) {
        Text("SWARM", color = NeuralCyan, fontSize = 12.sp)
        Text("Engines", color = MaterialTheme.colorScheme.onBackground, fontSize = 28.sp, fontWeight = FontWeight.Light)
        Spacer(Modifier.height(16.dp))

        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(engines.size) { i ->
                val e = engines[i]
                val statusColor = if (e.healthy) NeuralGreen else NeuralRed
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(4.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Box(
                        modifier = Modifier
                            .size(8.dp)
                            .padding(0.dp)
                    )
                    Spacer(Modifier.width(8.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text(e.engine, color = MaterialTheme.colorScheme.onBackground, fontSize = 14.sp)
                        Text(e.endpoint, color = NeuralMuted, fontSize = 10.sp)
                    }
                    Text(
                        "${(e.load * 100).toInt()}%",
                        color = if (e.load > 0.7f) com.aigestion.mobile.ui.theme.NeuralAmber else NeuralGreen,
                        fontSize = 12.sp,
                    )
                }
                Divider(color = MaterialTheme.colorScheme.surfaceVariant)
            }
        }
    }
}
