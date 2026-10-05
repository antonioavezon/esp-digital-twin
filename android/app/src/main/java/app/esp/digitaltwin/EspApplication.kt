package app.esp.digitaltwin

import android.app.Application
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.os.LocaleListCompat
import app.esp.digitaltwin.data.Preferences
import app.esp.digitaltwin.data.loadBundled
import app.esp.digitaltwin.engine.BundledContent
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.flow.first

class EspApplication : Application() {
    lateinit var preferences: Preferences
        private set
    val library = MutableStateFlow<BundledContent?>(null)
    val libraryError = MutableStateFlow(false)

    override fun onCreate() {
        super.onCreate()
        preferences = Preferences(this)
        val language = runBlocking { preferences.language.first() }
        AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags(language))
        CoroutineScope(Dispatchers.IO).launch {
            try {
                library.value = loadBundled(this@EspApplication)
            } catch (_: Exception) {
                libraryError.value = true
            }
        }
    }
}
