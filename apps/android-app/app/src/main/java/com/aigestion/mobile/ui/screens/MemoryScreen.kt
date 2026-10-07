package com.aigestion.mobile.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aigestion.mobile.ui.theme.NeuralCyan
import com.aigestion.mobile.ui.theme.NeuralGreen
import com.aigestion.mobile.ui.theme.NeuralMagenta
import com.aigestion.mobile.ui.theme.NeuralMuted

@Composable
fun MemoryScreen(innerPadding: PaddingValues) {
    val tiers = remember {
        listOf(
            Triple("episodic", 4210, NeuralCyan),
            Triple("semantic", 6180, NeuralMagenta),
            Triple("procedural", 2090, NeuralGreen),
        )
    }
    val total = tiers.sumOf { it.second }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(innerPadding)
            .padding(16.dp)
    ) {
        Text("VAULT", color = NeuralCyan, fontSize = 12.sp)
        Text("Memory", color = MaterialTheme.colorScheme.onBackground, fontSize = 28.sp, fontWeight = FontWeight.Light)
        Spacer(Modifier.height(16.dp))

        Text(total.toLocaleString(), color = MaterialTheme.colorScheme.onBackground, fontSize = 36.sp, fontWeight = FontWeight.Light)
        Text("TOTAL NODES", color = NeuralMuted, fontSize = 10.sp)
        Spacer(Modifier.height(16.dp))

        tiers.forEach { (name, count, color) ->
            val pct = if (total > 0) count.toFloat() / total else 0f
            Column(modifier = Modifier.padding(vertical = 6.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(name, color = color, fontSize = 13.sp)
                    Text(count.toLocaleString(), color = NeuralMuted, fontSize = 12.sp)
                }
                Spacer(Modifier.height(4.dp))
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(6.dp)
                        .clip(RoundedCornerShape(3.dp))
                        .background(MaterialTheme.colorScheme.surfaceVariant)
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth(pct)
                            .height(6.dp)
                            .clip(RoundedCornerShape(3.dp))
                            .background(color)
                    )
                }
            }
        }
    }
}

private fun Int.toLocaleString(): String =
    this.toString().replace(Regex("(\\d)(?=(\\d{3})+$)"), "$1,")
