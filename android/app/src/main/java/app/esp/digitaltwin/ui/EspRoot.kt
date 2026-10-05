package app.esp.digitaltwin.ui

import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.ScaffoldDefaults
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.TextButton
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationRail
import androidx.compose.material3.NavigationRailItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import app.esp.digitaltwin.R
import app.esp.digitaltwin.data.Preferences
import app.esp.digitaltwin.engine.BundledContent

private data class Tab(val route: String, val label: Int)

private val tabs = listOf(
    Tab("esp", R.string.nav_esp),
    Tab("pump", R.string.nav_pump),
    Tab("lab", R.string.nav_lab),
    Tab("curves", R.string.nav_curves),
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EspRoot(
    session: SessionViewModel,
    library: BundledContent?,
    libraryFailed: Boolean,
    language: String,
    dark: Boolean,
    preferences: Preferences,
) {
    val nav = rememberNavController()
    val backStack by nav.currentBackStackEntryAsState()
    val route = backStack?.destination?.route ?: "esp"
    var menu by remember { mutableStateOf(false) }
    fun go(target: String) {
        nav.navigate(target) {
            popUpTo(nav.graph.findStartDestination().id) { saveState = true }
            launchSingleTop = true
            restoreState = true
        }
    }
    val expanded = session.chartExpanded
    BoxWithConstraints(Modifier.fillMaxSize()) {
        val wide = maxWidth >= 840.dp && !expanded
        Scaffold(
            contentWindowInsets = if (expanded) WindowInsets(0.dp, 0.dp, 0.dp, 0.dp) else ScaffoldDefaults.contentWindowInsets,
            topBar = {
                if (!expanded) TopAppBar(
                    title = { Text(stringResource(R.string.app_name)) },
                    actions = {
                        TextButton(onClick = { menu = true }) {
                            Text(stringResource(R.string.menu))
                        }
                        DropdownMenu(expanded = menu, onDismissRequest = { menu = false }) {
                            DropdownMenuItem(
                                text = { Text(stringResource(R.string.nav_settings)) },
                                onClick = { menu = false; nav.navigate("settings") },
                            )
                            DropdownMenuItem(
                                text = { Text(stringResource(R.string.nav_about)) },
                                onClick = { menu = false; nav.navigate("about") },
                            )
                        }
                    },
                )
            },
            bottomBar = {
                if (!wide && !expanded) {
                    NavigationBar {
                        tabs.forEach { tab ->
                            NavigationBarItem(
                                selected = route == tab.route,
                                onClick = { go(tab.route) },
                                label = { Text(stringResource(tab.label)) },
                                icon = { Text(stringResource(tab.label).take(1)) },
                            )
                        }
                    }
                }
            },
        ) { padding ->
            Row(Modifier.fillMaxSize().padding(if (expanded) PaddingValues(0.dp) else padding)) {
                if (wide) {
                    NavigationRail {
                        tabs.forEach { tab ->
                            NavigationRailItem(
                                selected = route == tab.route,
                                onClick = { go(tab.route) },
                                label = { Text(stringResource(tab.label)) },
                                icon = { Text(stringResource(tab.label).take(1)) },
                            )
                        }
                    }
                }
                NavHost(
                    navController = nav,
                    startDestination = "esp",
                    modifier = Modifier.weight(1f).padding(if (expanded) 0.dp else 16.dp),
                ) {
                    composable("esp") { Body(library, libraryFailed) { EspScreen(it, language, session) } }
                    composable("pump") { Body(library, libraryFailed) { PumpScreen(it, session) } }
                    composable("lab") { LabScreen(session) }
                    composable("curves") { Body(library, libraryFailed) { CurvesScreen(it, session) } }
                    composable("settings") { SettingsScreen(language, dark, preferences) }
                    composable("about") { AboutScreen() }
                }
            }
        }
    }
}

@Composable
private fun Body(library: BundledContent?, failed: Boolean, content: @Composable (BundledContent) -> Unit) {
    when {
        library != null -> content(library)
        failed -> Text(stringResource(R.string.catalog_error))
        else -> Text(stringResource(R.string.loading_catalog))
    }
}
