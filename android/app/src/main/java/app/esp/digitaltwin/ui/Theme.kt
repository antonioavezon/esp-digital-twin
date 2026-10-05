package app.esp.digitaltwin.ui

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val Amber = Color(0xFFE0A84A)
private val AmberInk = Color(0xFF2A2316)
private val Teal = Color(0xFF3CBFB6)
private val Ink = Color(0xFFE7EEF6)
private val Night = Color(0xFF0C1116)
private val Panel = Color(0xFF141C25)
private val Panel2 = Color(0xFF1B2632)
private val Power = Color(0xFFD28B8B)

private val DarkColors = darkColorScheme(
    primary = Amber,
    onPrimary = AmberInk,
    secondary = Teal,
    background = Night,
    surface = Panel,
    surfaceVariant = Panel2,
    onBackground = Ink,
    onSurface = Ink,
    onSurfaceVariant = Color(0xFFC5D0DC),
    error = Power,
    outline = Color(0xFF3A4A5C),
)

private val LightColors = lightColorScheme(
    primary = Color(0xFF8A5A10),
    onPrimary = Color(0xFFFFF6E4),
    secondary = Color(0xFF0E6E68),
    background = Color(0xFFF4F7FB),
    surface = Color.White,
    surfaceVariant = Color(0xFFE7EEF6),
    onBackground = Color(0xFF14202B),
    onSurface = Color(0xFF14202B),
    error = Color(0xFF8C3A3A),
)

@Composable
fun EspTheme(dark: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = if (dark) DarkColors else LightColors, content = content)
}
