package app.esp.digitaltwin

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.lifecycle.viewmodel.compose.viewModel
import app.esp.digitaltwin.ui.EspRoot
import app.esp.digitaltwin.ui.EspTheme
import app.esp.digitaltwin.ui.SessionViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val app = application as EspApplication
        setContent {
            val dark by app.preferences.darkTheme.collectAsState(initial = true)
            val language by app.preferences.language.collectAsState(initial = "es")
            val library by app.library.collectAsState()
            val failed by app.libraryError.collectAsState()
            EspTheme(dark = dark) {
                val session: SessionViewModel = viewModel(factory = SessionViewModel.factory(app.preferences))
                EspRoot(
                    session = session,
                    library = library,
                    libraryFailed = failed,
                    language = language,
                    dark = dark,
                    preferences = app.preferences,
                )
            }
        }
    }
}
