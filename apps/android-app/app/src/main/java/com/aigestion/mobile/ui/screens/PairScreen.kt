package com.aigestion.mobile.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aigestion.mobile.ui.theme.NeuralCyan
import com.aigestion.mobile.ui.theme.NeuralGreen
import com.aigestion.mobile.ui.theme.NeuralMuted
import com.aigestion.mobile.pairing.PairingManager

@Composable
fun PairScreen(innerPadding: PaddingValues) {
    var pairCode by remember { mutableStateOf("······") }
    var status by remember { mutableStateOf("idle") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(innerPadding)
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("PC ↔ PIXEL", color = NeuralCyan, fontSize = 12.sp)
        Text("Pair device", color = MaterialTheme.colorScheme.onBackground, fontSize = 28.sp, fontWeight = FontWeight.Light)
        Text(
            "Challenge-response pairing. The shared secret never leaves either device.",
            color = NeuralMuted, fontSize = 12.sp,
            modifier = Modifier.padding(vertical = 8.dp),
        )

        Spacer(Modifier.height(24.dp))

        Surface(
            shape = MaterialTheme.shapes.large,
            color = MaterialTheme.colorScheme.surface,
            modifier = Modifier.padding(16.dp),
        ) {
            Column(
                modifier = Modifier.padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                Text("PAIR CODE", color = NeuralMuted, fontSize = 10.sp)
                Text(pairCode, color = NeuralCyan, fontSize = 28.sp, fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(8.dp))
                Text(status, color = NeuralMuted, fontSize = 12.sp)
            }
        }

        Spacer(Modifier.height(16.dp))

        Button(onClick = { /* TODO: call gateway /api/pair/challenge */ }) {
            Text("Start pairing")
        }
    }
}
