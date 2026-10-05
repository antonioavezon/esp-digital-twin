package app.esp.digitaltwin.ui

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import app.esp.digitaltwin.R
import app.esp.digitaltwin.data.LabSnapshot
import app.esp.digitaltwin.engine.DENSITY_UNITS
import app.esp.digitaltwin.engine.Experiments
import app.esp.digitaltwin.engine.FLOW_UNITS
import app.esp.digitaltwin.engine.HydraulicsResult
import app.esp.digitaltwin.engine.Measured
import app.esp.digitaltwin.engine.ModelException
import app.esp.digitaltwin.engine.PRESSURE_UNITS
import app.esp.digitaltwin.engine.Quantity
import app.esp.digitaltwin.engine.compareFluids
import app.esp.digitaltwin.engine.formatG6
import app.esp.digitaltwin.engine.parseDecimal
import app.esp.digitaltwin.engine.parseLabStages
import app.esp.digitaltwin.engine.runHydraulics

@Composable
fun LabScreen(session: SessionViewModel) {
    LaunchedEffect(Unit) { session.prefillIfNeeded() }
    Column(Modifier.fillMaxSize()) {
        LabMeter(session.result, Modifier.fillMaxWidth().height(180.dp))
        Column(Modifier.weight(1f).verticalScroll(rememberScrollState())) {
            BoxWithConstraints(Modifier.fillMaxWidth()) {
                if (maxWidth >= 700.dp) {
                    Row(Modifier.fillMaxWidth()) {
                        Column(Modifier.weight(1f)) { Inputs(session) }
                        Column(Modifier.weight(1f)) { Results(session) }
                    }
                } else {
                    Column(Modifier.fillMaxWidth()) {
                        Inputs(session)
                        Results(session)
                    }
                }
            }
        }
        Column(Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 4.dp)) {
            FrequencyCard(session)
        }
    }
}

@Composable
private fun LabMeter(result: HydraulicsResult?, modifier: Modifier) {
    val motion = rememberInfiniteTransition(label = "lab")
    val rise by motion.animateFloat(0f, 1f, infiniteRepeatable(tween(1200, easing = LinearEasing)), label = "rise")
    Canvas(modifier) {
        drawRect(Color(0xFF101820))
        val mid = size.width / 2f
        drawRoundRect(
            Color(0xFF1A2940),
            topLeft = Offset(mid - 36f, 16f),
            size = Size(72f, size.height - 32f),
            cornerRadius = CornerRadius(8f, 8f),
            style = Stroke(2f),
        )
        val travel = (size.height - 48f) * (1f - rise)
        drawCircle(Color(0xFF3CBFB6), 7f, Offset(mid, 28f + travel))
        drawContext.canvas.nativeCanvas.apply {
            val paint = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
                color = android.graphics.Color.WHITE
                textAlign = android.graphics.Paint.Align.CENTER
                textSize = 28f
            }
            drawText(result?.head?.display ?: "—", mid, size.height * 0.42f, paint)
            paint.textSize = 22f
            paint.color = android.graphics.Color.parseColor("#E0A84A")
            drawText(result?.deltaP?.display ?: "—", mid, size.height * 0.62f, paint)
        }
    }
}

@Composable
private fun Inputs(session: SessionViewModel) {
    Panel(stringResource(R.string.inputs)) {
        MeasureRow(stringResource(R.string.intake), session.intake, { session.intake = it }, session.intakeUnit, PRESSURE_UNITS) { session.intakeUnit = it }
        MeasureRow(stringResource(R.string.discharge), session.discharge, { session.discharge = it }, session.dischargeUnit, PRESSURE_UNITS) { session.dischargeUnit = it }
        MeasureRow(stringResource(R.string.density), session.density, { session.density = it }, session.densityUnit, DENSITY_UNITS) { session.densityUnit = it }
        MeasureRow(stringResource(R.string.flow), session.flow, { session.flow = it }, session.flowUnit, FLOW_UNITS) { session.flowUnit = it }
        NumberField(stringResource(R.string.stages), session.stages) { session.stages = it }
        InlineError(shortIssue(session.formError))
        PrimaryAction(stringResource(R.string.calculate)) {
            val intake = parseDecimal(session.intake)
            val discharge = parseDecimal(session.discharge)
            val density = parseDecimal(session.density)
            val flow = parseDecimal(session.flow)
            val stages = parseLabStages(session.stages)
            if (intake == null || discharge == null || density == null || flow == null) {
                session.formError = "number"
                session.result = null
                session.snapshot = null
                return@PrimaryAction
            }
            if (stages == null) {
                session.formError = "stages"
                session.result = null
                session.snapshot = null
                return@PrimaryAction
            }
            try {
                val result = runHydraulics(
                    Measured(intake, session.intakeUnit),
                    Measured(discharge, session.dischargeUnit),
                    Measured(density, session.densityUnit),
                    Measured(flow, session.flowUnit),
                    stages,
                )
                session.result = result
                session.snapshot = LabSnapshot(result.flow.siValue, result.head.siValue, result.power.siValue, result.density.siValue, stages)
                session.formError = null
            } catch (exc: ModelException) {
                session.formError = exc.code
                session.result = null
                session.snapshot = null
            }
        }
        Text(stringResource(R.string.experiments), style = MaterialTheme.typography.titleSmall)
        Experiments.all.forEach { experiment ->
            val label = when (experiment.id) {
                "base-water" -> "Caso base"
                "higher-differential" -> "Mayor ΔP"
                else -> "Otra densidad"
            }
            val selected = session.experimentId == experiment.id
            val onClick = { session.applyExperiment(experiment) }
            if (selected) {
                Button(onClick = onClick, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text(label) }
            } else {
                OutlinedButton(onClick = onClick, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text(label) }
            }
        }
        Text(stringResource(R.string.compare_title), style = MaterialTheme.typography.titleSmall)
        OutlinedTextField(session.fluidA, { session.fluidA = it }, modifier = Modifier.fillMaxWidth(), label = { Text(stringResource(R.string.fluid_a)) }, singleLine = true)
        NumberField(stringResource(R.string.density_a), session.densityA) { session.densityA = it }
        OutlinedTextField(session.fluidB, { session.fluidB = it }, modifier = Modifier.fillMaxWidth(), label = { Text(stringResource(R.string.fluid_b)) }, singleLine = true)
        NumberField(stringResource(R.string.density_b), session.densityB) { session.densityB = it }
        InlineError(shortIssue(session.compareError))
        PrimaryAction(stringResource(R.string.compare)) {
            val intake = parseDecimal(session.intake)
            val discharge = parseDecimal(session.discharge)
            val flow = parseDecimal(session.flow)
            val a = parseDecimal(session.densityA)
            val b = parseDecimal(session.densityB)
            if (intake == null || discharge == null || flow == null || a == null || b == null) {
                session.compareError = "number"
                session.compare = null
                return@PrimaryAction
            }
            try {
                session.compare = compareFluids(
                    Measured(intake, session.intakeUnit),
                    Measured(discharge, session.dischargeUnit),
                    Measured(flow, session.flowUnit),
                    listOf(session.fluidA to Measured(a, session.densityUnit), session.fluidB to Measured(b, session.densityUnit)),
                )
                session.compareError = null
            } catch (exc: ModelException) {
                session.compareError = exc.code
                session.compare = null
            }
        }
        session.compare?.let { compare ->
            Text(if (compare.lessonCode == "density") "Head distinto" else "Mismo head")
            compare.cases.forEach { case ->
                Text(case.name, style = MaterialTheme.typography.titleSmall)
                Text("ΔP ${case.result.deltaP.display} · H ${case.result.head.display} · P ${case.result.power.display}")
            }
        }
    }
}

@Composable
private fun MeasureRow(
    label: String,
    value: String,
    onValue: (String) -> Unit,
    unit: String,
    units: List<String>,
    onUnit: (String) -> Unit,
) {
    Row(
        Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f)) { NumberField(label, value, onValue = onValue) }
        UnitMenu(unit, units, Modifier.weight(0.7f), onUnit)
    }
}

@Composable
private fun Results(session: SessionViewModel) {
    Panel(stringResource(R.string.results)) {
        val result = session.result
        if (result == null) {
            Text("Sin cálculo")
        } else {
            Text("ΔP ${result.deltaP.display}")
            Text("Head ${result.head.display}")
            Text("Potencia ${result.power.display}")
            result.stageHead?.let { Text("Etapa ${it.display}") }
            if (result.warnings.isNotEmpty()) Text("Revisar datos", color = MaterialTheme.colorScheme.error)
        }
    }
}

@Composable
private fun QuantityRow(label: String, quantity: Quantity) {
    Text("$label: ${quantity.display}")
    Text(
        stringResource(R.string.quantity_meta, quantity.role, quantity.source, quantity.siUnit),
        style = MaterialTheme.typography.bodySmall,
    )
    if (quantity.presentations.isNotEmpty()) {
        val text = quantity.presentations.entries.joinToString(" · ") { "${formatG6(it.value)} ${it.key}" }
        Text(text, style = MaterialTheme.typography.bodySmall)
    }
}

private fun shortIssue(code: String?): String? = when (code) {
    null -> null
    "number" -> "Número inválido"
    "stages" -> "Etapas 1–120"
    "pressure_negative" -> "Presión negativa"
    "flow_negative" -> "Caudal negativo"
    "density_positive" -> "Densidad nula"
    "name" -> "Falta nombre"
    else -> "Dato inválido"
}
