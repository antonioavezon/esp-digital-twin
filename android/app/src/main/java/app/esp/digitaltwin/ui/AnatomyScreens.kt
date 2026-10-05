package app.esp.digitaltwin.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import app.esp.digitaltwin.R
import app.esp.digitaltwin.engine.BundledContent
import app.esp.digitaltwin.engine.text

@Composable
fun ScreenScroll(content: @Composable () -> Unit) {
    Column(
        Modifier.fillMaxWidth().verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) { content() }
}

@Composable
fun EspScreen(library: BundledContent, language: String, session: SessionViewModel) {
    var picked by remember { mutableStateOf<String?>(null) }
    Column(Modifier.fillMaxSize()) {
        WellSchematic(
            running = session.conceptualRun,
            energy = session.showEnergy,
            fluid = session.showFluid,
            selected = picked,
            onSelect = { picked = if (picked == it) null else it },
            modifier = Modifier.weight(1f).fillMaxWidth(),
        )
        Text(
            labelOf(picked),
            modifier = Modifier.padding(top = 4.dp),
            color = MaterialTheme.colorScheme.primary,
        )
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(
                onClick = {
                    session.conceptualRun = true
                    session.showEnergy = true
                    session.showFluid = true
                },
                modifier = Modifier.weight(1f).heightIn(min = 48.dp),
            ) { Text(stringResource(R.string.start)) }
            OutlinedButton(
                onClick = { session.conceptualRun = false },
                modifier = Modifier.weight(1f).heightIn(min = 48.dp),
            ) { Text(stringResource(R.string.stop)) }
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            FilterChip(
                selected = session.showEnergy,
                onClick = { session.showEnergy = !session.showEnergy },
                label = { Text(if (language == "en") "Energy" else "Energía") },
                modifier = Modifier.weight(1f),
            )
            FilterChip(
                selected = session.showFluid,
                onClick = { session.showFluid = !session.showFluid },
                label = { Text(if (language == "en") "Fluid" else "Fluido") },
                modifier = Modifier.weight(1f),
            )
        }
    }
    library.esp.text("id")
}

private fun labelOf(id: String?): String = when (id) {
    "power-supply" -> "Alimentación"
    "vsd" -> "Regulador"
    "electrical-cable" -> "Cable"
    "production-flow" -> "Flujo"
    "reservoir" -> "Reservorio"
    "surface" -> "Superficie"
    "well" -> "Pozo"
    "tubing" -> "Tubing"
    "pump" -> "Bomba"
    "intake" -> "Admisión"
    "protector" -> "Protector"
    "motor" -> "Motor"
    "shaft" -> "Eje"
    else -> ""
}

@Composable
fun PumpScreen(library: BundledContent, session: SessionViewModel) {
    var playing by remember { mutableStateOf(true) }
    var fluid by remember { mutableStateOf(true) }
    var multi by remember { mutableStateOf(true) }
    val stages = if (multi) 3 else 1
    Column(Modifier.fillMaxSize()) {
        PumpGraphic(
            playing = playing,
            showFluid = fluid,
            stages = stages,
            selected = session.pumpPartId,
            onSelect = { session.pumpPartId = if (session.pumpPartId == it) null else it },
            modifier = Modifier.weight(1f).fillMaxWidth(),
        )
        Text(
            when (session.pumpPartId) {
                "impeller" -> "Impulsor gira"
                "diffuser" -> "Difusor fijo"
                else -> ""
            },
            color = MaterialTheme.colorScheme.primary,
        )
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { playing = !playing }, modifier = Modifier.weight(1f).heightIn(min = 48.dp)) {
                Text(if (playing) "Pausa" else "Gira")
            }
            OutlinedButton(onClick = { fluid = !fluid }, modifier = Modifier.weight(1f).heightIn(min = 48.dp)) {
                Text(if (fluid) "Fluido" else "Sin fluido")
            }
            OutlinedButton(onClick = { multi = !multi }, modifier = Modifier.weight(1f).heightIn(min = 48.dp)) {
                Text(if (multi) "3 etapas" else "1 etapa")
            }
        }
    }
    library.pump.text("id")
}
