package app.esp.digitaltwin.ui

import androidx.appcompat.app.AppCompatDelegate
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.res.stringResource
import androidx.core.os.LocaleListCompat
import app.esp.digitaltwin.R
import app.esp.digitaltwin.data.Preferences
import app.esp.digitaltwin.engine.PHYSICS_MODE
import app.esp.digitaltwin.engine.PHYSICS_MODEL
import kotlinx.coroutines.launch
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun SettingsScreen(language: String, dark: Boolean, preferences: Preferences) {
    val scope = rememberCoroutineScope()
    ScreenScroll {
        Panel(stringResource(R.string.nav_settings)) {
            Text(stringResource(R.string.settings_body))
            Text(stringResource(R.string.language), modifier = Modifier.heightIn(min = 48.dp))
            LanguageRow(stringResource(R.string.spanish), language == "es") {
                scope.launch {
                    preferences.setLanguage("es")
                    AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags("es"))
                }
            }
            LanguageRow(stringResource(R.string.english), language == "en") {
                scope.launch {
                    preferences.setLanguage("en")
                    AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags("en"))
                }
            }
            Text(stringResource(R.string.theme))
            LanguageRow(stringResource(R.string.dark), dark) { scope.launch { preferences.setDark(true) } }
            LanguageRow(stringResource(R.string.light), !dark) { scope.launch { preferences.setDark(false) } }
        }
    }
}

@Composable
private fun LanguageRow(label: String, selected: Boolean, onClick: () -> Unit) {
    Row(Modifier.fillMaxWidth().heightIn(min = 48.dp), verticalAlignment = Alignment.CenterVertically) {
        RadioButton(selected = selected, onClick = onClick)
        Text(label)
    }
}

@Composable
fun AboutScreen() {
    ScreenScroll {
        Panel(stringResource(R.string.about_project)) {
            Text(stringResource(R.string.about_p1))
            Text(stringResource(R.string.about_p2))
        }
        Panel(stringResource(R.string.about_research)) {
            Text("Virtual Research Internship (VRI)")
            Text(stringResource(R.string.research_title_en))
            Text(stringResource(R.string.research_title_es))
        }
        Panel(stringResource(R.string.about_status)) {
            Text(stringResource(R.string.status_stage, "1C"))
            Text(stringResource(R.string.status_model, PHYSICS_MODEL))
            Text(stringResource(R.string.status_mode, PHYSICS_MODE))
            Text(stringResource(R.string.status_note))
        }
        Panel(stringResource(R.string.about_roadmap)) {
            Road("1A", "Anatomy", stringResource(R.string.hint_1a))
            Road("1B", "Multistage Pump", stringResource(R.string.hint_1b))
            Road("1C", "Basic Hydraulics", stringResource(R.string.hint_1c))
            Road("1D", "Pump Performance Curves", stringResource(R.string.hint_1d))
            Road("1E", "Motor", stringResource(R.string.hint_1e))
            Road("1F", "VSD/VFD", stringResource(R.string.hint_1f))
        }
        Panel(stringResource(R.string.about_author)) {
            Text("Antonio Ralph Avezon Saavedra")
            Text(stringResource(R.string.author_role))
            Text(stringResource(R.string.author_study))
        }
        Panel(stringResource(R.string.about_academic)) {
            Text("Universidad Andrés Bello — Chile")
            Text(stringResource(R.string.academic_origin))
            Text("Universidad de los Andes — Colombia")
            Text(stringResource(R.string.academic_host))
            Text("Hemispheric University Consortium (HUC)")
            Text("Virtual Research Internship Program")
            Text("Hybrid Physics-AI Model for Sensorless Monitoring and Anomaly Detection in Electrical Submersible Pump Systems")
            Text(stringResource(R.string.role_supervisor))
            Text("Nicolás Rios Ratkovich — Universidad de los Andes, Colombia")
        }
        Panel(stringResource(R.string.about_stack)) {
            Text("Python, Django, FastAPI, JavaScript, HTML5, CSS, SVG, Podman, Kotlin, Jetpack Compose")
        }
        Panel(stringResource(R.string.about_planned)) {
            Text(stringResource(R.string.planned_body))
        }
        Panel(stringResource(R.string.about_use)) {
            Text(stringResource(R.string.about_use_body))
        }
        Text("ESP Digital Twin\n${stringResource(R.string.developed)} Antonio Ralph Avezon Saavedra\n2026")
    }
}

@Composable
private fun Road(id: String, name: String, hint: String) {
    Text("$id  $name  ${stringResource(R.string.roadmap_done)}")
    Text(hint)
}
