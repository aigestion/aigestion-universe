package com.aigestion.mobile.ui.screens

import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.foundation.layout.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aigestion.mobile.ui.components.NeuralCard
import com.aigestion.mobile.ui.theme.NeuralCyan
import com.aigestion.mobile.ui.theme.NeuralGreen
import com.aigestion.mobile.ui.theme.NeuralMagenta
import com.aigestion.mobile.ui.theme.NeuralMuted

@Composable
fun HomeScreen(innerPadding: PaddingValues) {
    val tiles = listOf(
        Triple("Coherence", "L4", NeuralCyan),
        Triple("Empathy", "96%", NeuralMagenta),
        Triple("Nodes", "12,480", NeuralGreen),
        Triple("Engines", "19", NeuralCyan),
    )

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(innerPadding)
            .padding(16.dp)
    ) {
        Text("DANIELA OS", color = NeuralCyan, fontSize = 12.sp, fontWeight = FontWeight.Medium)
        Text(
            "Neural Core",
            color = MaterialTheme.colorScheme.onBackground,
            fontSize = 28.sp,
            fontWeight = FontWeight.Light,
        )
        Spacer(Modifier.height(16.dp))

        LazyVerticalGrid(
            columns = GridCells.Fixed(2),
            contentPadding = PaddingValues(4.dp),
            modifier = Modifier.fillMaxWidth(),
        ) {
            items(tiles.size) { i ->
                val (label, value, color) = tiles[i]
                NeuralCard(accent = color, modifier = Modifier.padding(4.dp)) {
                    Text(label, color = NeuralMuted, fontSize = 11.sp)
                    Spacer(Modifier.height(4.dp))
                    Text(value, color = color, fontSize = 22.sp, fontWeight = FontWeight.SemiBold)
                }
            }
        }
    }
}
