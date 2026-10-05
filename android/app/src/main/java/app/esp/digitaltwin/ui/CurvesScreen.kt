package app.esp.digitaltwin.ui

import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import android.content.pm.ActivityInfo
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.ui.Alignment
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Checkbox
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import app.esp.digitaltwin.engine.BundledContent
import app.esp.digitaltwin.engine.FLOW_UNITS
import app.esp.digitaltwin.engine.HEAD_UNITS
import app.esp.digitaltwin.engine.ModelException
import app.esp.digitaltwin.engine.POWER_UNITS
import app.esp.digitaltwin.engine.PresentedCurve
import app.esp.digitaltwin.engine.RawCurve
import app.esp.digitaltwin.engine.domain
import app.esp.digitaltwin.engine.formatG6
import app.esp.digitaltwin.engine.nearestSample
import app.esp.digitaltwin.engine.parseCurveStages
import app.esp.digitaltwin.engine.presentCurve
import app.esp.digitaltwin.engine.withLabMarker

private fun speedOf(curve: RawCurve) = "${formatG6(curve.frequencyHz)} Hz / ${formatG6(curve.speedRpm)} rpm"

private fun Context.findActivity(): Activity? {
    var current: Context? = this
    while (current is ContextWrapper) {
        if (current is Activity) return current
        current = current.baseContext
    }
    return null
}

@Composable
fun CurvesScreen(library: BundledContent, session: SessionViewModel) {
    val curves = library.curves
    LaunchedEffect(curves) {
        if (session.manufacturer.isBlank() && curves.isNotEmpty()) {
            val first = curves.first()
            session.manufacturer = first.manufacturer
            session.series = first.series
            session.model = first.model
            session.speed = speedOf(first)
        }
    }
    val manufacturers = curves.map { it.manufacturer }.distinct()
    val series = curves.filter { it.manufacturer == session.manufacturer }.map { it.series }.distinct()
    val models = curves.filter { it.manufacturer == session.manufacturer && it.series == session.series }.map { it.model }.distinct()
    val speeds = curves.filter {
        it.manufacturer == session.manufacturer && it.series == session.series && it.model == session.model
    }.map { speedOf(it) }.distinct()
    val raw = curves.find {
        it.manufacturer == session.manufacturer && it.series == session.series && it.model == session.model && speedOf(it) == session.speed
    }
    val context = LocalContext.current
    fun landscape() {
        context.findActivity()?.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE
    }
    fun portrait() {
        context.findActivity()?.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_PORTRAIT
    }
    LaunchedEffect(session.chartExpanded) {
        if (session.chartExpanded) landscape()
    }
    DisposableEffect(Unit) {
        onDispose {
            if (session.chartExpanded) {
                session.chartExpanded = false
                portrait()
            }
        }
    }
    val stagesResult = runCatching { parseCurveStages(session.curveStages) }
    val error = (stagesResult.exceptionOrNull() as? ModelException)?.code
    val presented = if (raw != null && error == null && (session.showHead || session.showPower || session.showEfficiency)) {
        runCatching {
            val stages = stagesResult.getOrNull()
            val base = presentCurve(raw, stages, session.curveFlowUnit, session.curveHeadUnit, session.curvePowerUnit)
            val snap = session.snapshot
            if (snap == null) base else withLabMarker(raw, base, stages, snap.flowM3s, snap.headM, snap.powerW, snap.density)
        }.getOrNull()
    } else {
        null
    }
    if (session.chartExpanded && presented != null) {
        Row(
            Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding().padding(4.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            OutlinedButton(
                onClick = {
                    portrait()
                    session.chartExpanded = false
                },
                modifier = Modifier.widthIn(max = 92.dp).heightIn(min = 48.dp),
            ) { Text("Volver") }
            CurvePlot(
                presented,
                session.showHead,
                session.showPower,
                session.showEfficiency,
                0,
                false,
                Modifier.weight(1f).fillMaxHeight(),
            )
        }
        return
    }
    Column(Modifier.fillMaxSize()) {
        if (presented != null) {
            CurvePlot(
                presented,
                session.showHead,
                session.showPower,
                session.showEfficiency,
                0,
                false,
                Modifier.weight(1f).fillMaxWidth(),
            )
        } else {
            Text(if (error != null) "Dato inválido" else "Sin curva", modifier = Modifier.weight(1f))
        }
        OutlinedButton(
            onClick = {
                session.chartExpanded = true
                landscape()
            },
            enabled = presented != null,
            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
        ) { Text("Pantalla") }
        presented?.let { Numbers(it, session) }
        Column(Modifier.heightIn(max = 220.dp).verticalScroll(rememberScrollState())) {
            ChoiceField("Fabricante", session.manufacturer, manufacturers) {
                session.manufacturer = it
                val next = curves.first { curve -> curve.manufacturer == it }
                session.series = next.series
                session.model = next.model
                session.speed = speedOf(next)
            }
            ChoiceField("Serie", session.series, series) {
                session.series = it
                val next = curves.first { curve -> curve.manufacturer == session.manufacturer && curve.series == it }
                session.model = next.model
                session.speed = speedOf(next)
            }
            ChoiceField("Modelo", session.model, models) {
                session.model = it
                session.speed = speedOf(curves.first { curve ->
                    curve.manufacturer == session.manufacturer && curve.series == session.series && curve.model == it
                })
            }
            ChoiceField("Velocidad", session.speed, speeds) { session.speed = it }
            NumberField("Etapas", session.curveStages) { session.curveStages = it }
            ChoiceField("Caudal", session.curveFlowUnit, FLOW_UNITS) { session.curveFlowUnit = it }
            ChoiceField("Head", session.curveHeadUnit, HEAD_UNITS) { session.curveHeadUnit = it }
            ChoiceField("Potencia", session.curvePowerUnit, POWER_UNITS) { session.curvePowerUnit = it }
            Toggle("Head", session.showHead) { session.showHead = it }
            Toggle("Eje", session.showPower) { session.showPower = it }
            Toggle("Eficiencia", session.showEfficiency) { session.showEfficiency = it }
        }
    }
}

@Composable
private fun Numbers(curve: PresentedCurve, session: SessionViewModel) {
    val bep = curve.bep
    if (bep != null) {
        Text(
            "BEP ${formatG6(bep.flow)} ${curve.flowUnit}",
            style = MaterialTheme.typography.bodyMedium,
        )
    }
    val samples = buildList {
        if (session.showHead) addAll(curve.head)
        if (session.showPower) addAll(curve.shaftPower)
        if (session.showEfficiency) addAll(curve.efficiency)
    }
    val span = domain(samples.map { it.flow }) ?: return
    var fraction by remember { mutableFloatStateOf(0.5f) }
    Slider(value = fraction, onValueChange = { fraction = it })
    val target = span.start + (span.endInclusive - span.start) * fraction
    nearestSample(if (session.showHead) curve.head else emptyList(), target)?.let {
        Text("Head ${formatG6(it.value)} ${curve.headUnit}")
    }
}

@Composable
private fun Toggle(label: String, checked: Boolean, onChange: (Boolean) -> Unit) {
    Row {
        Checkbox(checked = checked, onCheckedChange = onChange)
        Text(label)
    }
}
