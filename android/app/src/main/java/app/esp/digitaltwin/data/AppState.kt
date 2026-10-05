package app.esp.digitaltwin.data

import android.content.Context
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.doublePreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import app.esp.digitaltwin.engine.BundledContent
import app.esp.digitaltwin.engine.parseBundled
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import java.io.FileNotFoundException

private val Context.store by preferencesDataStore("esp-movil")

class Preferences(private val context: Context) {
    private val languageKey = stringPreferencesKey("language")
    private val darkKey = booleanPreferencesKey("dark")
    private val hzKey = doublePreferencesKey("study_hz")

    val language: Flow<String> = context.store.data.map { it[languageKey] ?: "es" }
    val darkTheme: Flow<Boolean> = context.store.data.map { it[darkKey] ?: true }
    val studyHz: Flow<Double> = context.store.data.map { it[hzKey] ?: 60.0 }

    suspend fun setLanguage(tag: String) {
        context.store.edit { it[languageKey] = tag }
    }

    suspend fun setDark(dark: Boolean) {
        context.store.edit { it[darkKey] = dark }
    }

    suspend fun setStudyHz(hz: Double) {
        context.store.edit { it[hzKey] = hz }
    }
}

fun loadBundled(context: Context): BundledContent {
    fun read(name: String) = context.assets.open(name).bufferedReader().use { it.readText() }
    try {
        return parseBundled(read("esp.json"), read("esp_en.json"), read("pump.json"), read("reda.json"))
    } catch (exc: FileNotFoundException) {
        throw IllegalStateException("catalog", exc)
    }
}

data class LabSnapshot(
    val flowM3s: Double,
    val headM: Double,
    val powerW: Double,
    val density: Double,
    val stages: Int,
)
