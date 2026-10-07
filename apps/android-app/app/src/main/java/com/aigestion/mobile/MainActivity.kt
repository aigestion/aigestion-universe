package com.aigestion.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Scaffold
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.aigestion.mobile.ui.screens.HomeScreen
import com.aigestion.mobile.ui.screens.PairScreen
import com.aigestion.mobile.ui.screens.EnginesScreen
import com.aigestion.mobile.ui.screens.MemoryScreen
import com.aigestion.mobile.ui.theme.AigestionTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            AigestionTheme {
                val navController = rememberNavController()
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    NavHost(
                        navController = navController,
                        startDestination = "home",
                        modifier = Modifier.fillMaxSize(),
                    ) {
                        composable("home") { HomeScreen(innerPadding) }
                        composable("pair") { PairScreen(innerPadding) }
                        composable("engines") { EnginesScreen(innerPadding) }
                        composable("memory") { MemoryScreen(innerPadding) }
                    }
                }
            }
        }
    }
}
