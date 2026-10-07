package com.aigestion.mobile.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val DarkColorScheme = darkColorScheme(
    primary = NeuralCyan,
    onPrimary = Color.Black,
    secondary = NeuralMagenta,
    onSecondary = Color.Black,
    background = NeuralBg,
    onBackground = NeuralText,
    surface = NeuralPanel,
    onSurface = NeuralText,
    surfaceVariant = NeuralPanel,
    onSurfaceVariant = NeuralMuted,
    error = NeuralRed,
)

@Composable
fun AigestionTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = DarkColorScheme,
        content = content,
    )
}
