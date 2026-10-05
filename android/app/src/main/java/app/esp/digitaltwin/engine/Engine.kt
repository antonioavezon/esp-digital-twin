package app.esp.digitaltwin.engine

import java.util.Locale
import kotlin.math.abs

/** Mismas constantes que `esp-core` `app/physics/units.py` y `constants.py`. */
const val PHYSICS_MODEL = "hydraulics-v0.1"
const val PHYSICS_MODE = "static"
const val STANDARD_GRAVITY = 9.80665
const val DEFAULT_DENSITY = 1000.0
const val PSI_TO_PA = 6894.757293168361
const val BAR_TO_PA = 100_000.0
const val KPA_TO_PA = 1_000.0
const val BARREL_M3 = 0.158987294928
const val SECONDS_PER_DAY = 86_400.0
const val FT_TO_M = 0.3048
const val HP_TO_W = 745.6998715822702

const val LAB_STAGE_MIN = 1
const val LAB_STAGE_MAX = 120

class ModelException(val code: String) : Exception(code)

private val PRESSURE = mapOf("pa" to 1.0, "kpa" to KPA_TO_PA, "bar" to BAR_TO_PA, "psi" to PSI_TO_PA)
private val FLOW = mapOf(
    "m3/s" to 1.0,
    "m3/day" to 1.0 / SECONDS_PER_DAY,
    "bpd" to BARREL_M3 / SECONDS_PER_DAY,
)
private val DENSITY = mapOf("kg/m3" to 1.0)
private val HEAD = mapOf("m" to 1.0, "ft" to FT_TO_M)
private val POWER = mapOf("w" to 1.0, "kw" to 1000.0, "hp" to HP_TO_W)

val PRESSURE_UNITS = listOf("pa", "kpa", "bar", "psi")
val FLOW_UNITS = listOf("m3/s", "m3/day", "bpd")
val DENSITY_UNITS = listOf("kg/m3")
val HEAD_UNITS = listOf("ft", "m")
val POWER_UNITS = listOf("hp", "kW")

fun canonicalUnit(unit: String): String {
    val text = unit.trim().lowercase(Locale.US).replace("³", "3").replace("μ", "u").replace(" ", "")
    val aliases = mapOf(
        "m^3/s" to "m3/s",
        "m^3/day" to "m3/day",
        "m3/d" to "m3/day",
        "kg/m^3" to "kg/m3",
        "feet" to "ft",
        "kw" to "kw",
    )
    return aliases[text] ?: text
}

private fun factor(table: Map<String, Double>, unit: String, code: String): Double {
    val key = canonicalUnit(unit)
    return table[key] ?: throw ModelException(code)
}

fun toPascal(value: Double, unit: String) = value * factor(PRESSURE, unit, "pressure_unit")
fun fromPascal(value: Double, unit: String) = value / factor(PRESSURE, unit, "pressure_unit")
fun toM3s(value: Double, unit: String) = value * factor(FLOW, unit, "flow_unit")
fun fromM3s(value: Double, unit: String) = value / factor(FLOW, unit, "flow_unit")
fun toKgM3(value: Double, unit: String) = value * factor(DENSITY, unit, "density_unit")
fun fromMetres(value: Double, unit: String) = value / factor(HEAD, unit, "head_unit")
fun fromWatts(value: Double, unit: String) = value / factor(POWER, unit, "power_unit")

fun formatG6(value: Double): String {
    if (value.isNaN() || value.isInfinite()) return value.toString()
    val raw = String.format(Locale.US, "%.6g", value)
    if ('e' in raw || 'E' in raw || '.' !in raw) return raw
    return raw.trimEnd('0').trimEnd('.')
}

fun formatQuantity(value: Double, unit: String) = "${formatG6(value)} $unit"

data class Measured(val value: Double, val unit: String)

data class Quantity(
    val value: Double,
    val unit: String,
    val siValue: Double,
    val siUnit: String,
    val source: String,
    val role: String,
    val display: String,
    val presentations: Map<String, Double> = emptyMap(),
)

data class CalcStep(
    val titleCode: String,
    val equation: String,
    val substitution: String,
    val display: String,
    val interpretationCode: String,
    val extraEquation: String? = null,
    val extraSubstitution: String? = null,
    val extraDisplay: String? = null,
)

data class HydraulicsResult(
    val intake: Quantity,
    val discharge: Quantity,
    val density: Quantity,
    val flow: Quantity,
    val gravity: Quantity,
    val deltaP: Quantity,
    val head: Quantity,
    val power: Quantity,
    val powerFromPressureW: Double,
    val stageHead: Quantity?,
    val stageCount: Int?,
    val steps: List<CalcStep>,
    val warnings: List<String>,
)

data class CompareCase(val name: String, val result: HydraulicsResult)

data class CompareResult(
    val samePressure: Boolean,
    val sameHead: Boolean,
    val lessonCode: String,
    val cases: List<CompareCase>,
)

private fun pressurePresentations(pa: Double) = PRESSURE_UNITS.associateWith { fromPascal(pa, it) }
private fun flowPresentations(m3s: Double) = FLOW_UNITS.associateWith { fromM3s(m3s, it) }

fun runHydraulics(
    intake: Measured,
    discharge: Measured,
    density: Measured,
    flow: Measured,
    stages: Int?,
    gravity: Double = STANDARD_GRAVITY,
): HydraulicsResult {
    if (intake.value < 0 || discharge.value < 0) throw ModelException("pressure_negative")
    val intakePa = toPascal(intake.value, intake.unit)
    val dischargePa = toPascal(discharge.value, discharge.unit)
    val rho = try {
        toKgM3(density.value, density.unit)
    } catch (exc: ModelException) {
        throw exc
    }
    if (rho <= 0.0) throw ModelException("density_positive")
    if (flow.value < 0) throw ModelException("flow_negative")
    val q = toM3s(flow.value, flow.unit)
    if (stages != null && stages < 1) throw ModelException("stages")

    val delta = dischargePa - intakePa
    val head = delta / (rho * gravity)
    val power = rho * gravity * q * head
    val powerFromPressure = q * delta
    val warnings = mutableListOf<String>()
    if (dischargePa <= intakePa) warnings += "discharge_not_above_intake"
    if (q == 0.0) warnings += "zero_flow"

    val deltaDisplay = try {
        formatQuantity(fromPascal(delta, discharge.unit), discharge.unit)
    } catch (_: ModelException) {
        formatQuantity(delta, "Pa")
    }
    val stageHead = if (stages == null) {
        null
    } else {
        val perStage = head / stages
        Quantity(
            value = perStage,
            unit = "m",
            siValue = perStage,
            siUnit = "m",
            source = "physics_model",
            role = "calculated",
            display = formatQuantity(perStage, "m"),
        )
    }
    val steps = mutableListOf(
        CalcStep(
            titleCode = "delta",
            equation = "ΔP = P_discharge − P_intake",
            substitution = "ΔP = ${formatQuantity(dischargePa, "Pa")} − ${formatQuantity(intakePa, "Pa")}",
            display = "${formatQuantity(delta, "Pa")} ($deltaDisplay)",
            interpretationCode = "delta",
        ),
        CalcStep(
            titleCode = "head",
            equation = "H = ΔP / (ρ · g)",
            substitution = "H = ${formatQuantity(delta, "Pa")} / (${formatQuantity(rho, "kg/m³")} · ${formatQuantity(gravity, "m/s²")})",
            display = formatQuantity(head, "m"),
            interpretationCode = "head",
        ),
        CalcStep(
            titleCode = "power",
            equation = "P_hyd = ρ · g · Q · H",
            substitution = "P_hyd = ${formatQuantity(rho, "kg/m³")} · ${formatQuantity(gravity, "m/s²")} · ${formatQuantity(q, "m³/s")} · ${formatQuantity(head, "m")}",
            display = "${formatQuantity(power, "W")} (${formatQuantity(power / 1000.0, "kW")})",
            interpretationCode = "power",
            extraEquation = "P_hyd = Q · ΔP",
            extraSubstitution = "P_hyd = ${formatQuantity(q, "m³/s")} · ${formatQuantity(delta, "Pa")}",
            extraDisplay = formatQuantity(powerFromPressure, "W"),
        ),
    )
    if (stageHead != null && stages != null) {
        steps += CalcStep(
            titleCode = "stage",
            equation = "H_etapa = H_total / N",
            substitution = "H_etapa = ${formatQuantity(head, "m")} / $stages",
            display = stageHead.display,
            interpretationCode = "stage",
        )
    }
    fun inputQuantity(measured: Measured, si: Double, siUnit: String, display: String, presentations: Map<String, Double> = emptyMap()) =
        Quantity(measured.value, measured.unit, si, siUnit, "user_input", "input", display, presentations)

    return HydraulicsResult(
        intake = inputQuantity(intake, intakePa, "Pa", formatQuantity(intake.value, intake.unit), pressurePresentations(intakePa)),
        discharge = inputQuantity(discharge, dischargePa, "Pa", formatQuantity(discharge.value, discharge.unit), pressurePresentations(dischargePa)),
        density = inputQuantity(density, rho, "kg/m³", formatQuantity(rho, "kg/m³")),
        flow = inputQuantity(flow, q, "m³/s", formatQuantity(flow.value, flow.unit), flowPresentations(q)),
        gravity = Quantity(gravity, "m/s²", gravity, "m/s²", "constant", "constant", formatQuantity(gravity, "m/s²")),
        deltaP = Quantity(delta, "Pa", delta, "Pa", "physics_model", "calculated", deltaDisplay, pressurePresentations(delta)),
        head = Quantity(head, "m", head, "m", "physics_model", "calculated", formatQuantity(head, "m")),
        power = Quantity(
            power,
            "W",
            power,
            "W",
            "physics_model",
            "calculated",
            formatQuantity(power / 1000.0, "kW"),
            mapOf("W" to power, "kW" to power / 1000.0),
        ),
        powerFromPressureW = powerFromPressure,
        stageHead = stageHead,
        stageCount = stages,
        steps = steps,
        warnings = warnings,
    )
}

fun compareFluids(
    intake: Measured,
    discharge: Measured,
    flow: Measured,
    fluids: List<Pair<String, Measured>>,
): CompareResult {
    if (fluids.size < 2) throw ModelException("fluids")
    val cases = fluids.map { (name, density) ->
        if (name.isBlank()) throw ModelException("name")
        CompareCase(name, runHydraulics(intake, discharge, density, flow, stages = null))
    }
    val deltas = cases.map { it.result.deltaP.siValue }
    val heads = cases.map { it.result.head.siValue }
    val samePressure = deltas.all { abs(it - deltas[0]) <= 1e-6 }
    val sameHead = heads.all { abs(it - heads[0]) <= 1e-9 }
    val lesson = when {
        samePressure && !sameHead -> "density"
        samePressure && sameHead -> "same"
        else -> "pressure"
    }
    return CompareResult(samePressure, sameHead, lesson, cases)
}

data class Experiment(
    val id: String,
    val name: String,
    val objective: String,
    val disclaimer: String,
    val intake: Double,
    val discharge: Double,
    val density: Double,
    val flow: Double,
)

object Experiments {
    private const val NOTE = "Caso educativo. No es la especificación de una ESP comercial."
    val all = listOf(
        Experiment(
            "base-water",
            "Experiment 1 — Base",
            "Caso simple con densidad de agua. Sirve de referencia.",
            NOTE, 100.0, 300.0, DEFAULT_DENSITY, 500.0,
        ),
        Experiment(
            "higher-differential",
            "Experiment 2 — Higher Differential Pressure",
            "Misma densidad y mismo caudal. Mayor ΔP: observar head y potencia hidráulica.",
            NOTE, 100.0, 500.0, DEFAULT_DENSITY, 500.0,
        ),
        Experiment(
            "different-density",
            "Experiment 3 — Different Fluid Density",
            "Mismas presiones y mismo caudal que el caso base. Otra densidad: el head cambia.",
            NOTE, 100.0, 300.0, 850.0, 500.0,
        ),
    )
    val compareA = "Fluid A" to DEFAULT_DENSITY
    val compareB = "Fluid B" to 850.0
}

data class Sample(val flow: Double, val value: Double)

data class Bep(
    val origin: String,
    val flow: Double,
    val head: Double,
    val shaftPower: Double,
    val efficiencyPercent: Double,
)

data class Marker(
    val comparable: Boolean,
    val flow: Double?,
    val head: Double?,
    val hydraulicPower: Double,
    val shaftFromCurve: Double?,
    val efficiencyPercent: Double?,
    val estimate: Double?,
)

data class PresentedCurve(
    val id: String,
    val manufacturer: String,
    val series: String,
    val model: String,
    val frequencyHz: Double,
    val speedRpm: Double,
    val basisCode: String,
    val stages: Int?,
    val flowUnit: String,
    val headUnit: String,
    val powerUnit: String,
    val head: List<Sample>,
    val shaftPower: List<Sample>,
    val efficiency: List<Sample>,
    val bep: Bep?,
    val rangeName: String?,
    val rangeMin: Double?,
    val rangeMax: Double?,
    val warnings: List<String>,
    val digitizationWarning: String?,
    val sourceDocument: String,
    val sourcePage: String,
    val sourceQuality: String,
    val marker: Marker?,
)

fun interpolate(flows: DoubleArray, values: DoubleArray, flow: Double): Double? {
    if (flows.size < 2 || flows.size != values.size) return null
    val first = flows.first()
    val last = flows.last()
    if (flow < first || flow > last) return null
    for (index in 0 until flows.lastIndex) {
        val span = flows[index + 1] - flows[index]
        if (flows[index] <= flow && flow <= flows[index + 1] && span != 0.0) {
            val weight = (flow - flows[index]) / span
            return values[index] + weight * (values[index + 1] - values[index])
        }
    }
    return values.last()
}

fun nearestSample(samples: List<Sample>, flow: Double): Sample? {
    if (samples.isEmpty()) return null
    return samples.minBy { abs(it.flow - flow) }
}

fun domain(values: List<Double>): ClosedFloatingPointRange<Double>? {
    if (values.isEmpty()) return null
    val min = values.min()
    val max = values.max()
    return if (min == max) (min - 1.0)..(max + 1.0) else min..max
}

enum class HzIssue { EMPTY, INVALID }

fun parseStudyHz(raw: String, kept: Double): Pair<Double?, HzIssue?> {
    val text = raw.trim().replace(',', '.')
    if (text.isEmpty()) return kept to HzIssue.EMPTY
    val value = text.toDoubleOrNull()
    if (value == null || value < 30.0 || value > 90.0) return kept to HzIssue.INVALID
    return value to null
}

fun parseDecimal(raw: String): Double? {
    val text = raw.trim().replace(',', '.')
    if (text.isEmpty()) return null
    val value = text.toDoubleOrNull() ?: return null
    if (value.isNaN() || value.isInfinite()) return null
    return value
}

fun parseLabStages(raw: String): Int? {
    val value = raw.trim().toIntOrNull() ?: return null
    if (value !in LAB_STAGE_MIN..LAB_STAGE_MAX) return null
    return value
}

fun parseCurveStages(raw: String): Int? {
    if (raw.isBlank()) return null
    val value = raw.trim().toIntOrNull() ?: throw ModelException("stages")
    if (value < 1) throw ModelException("stages")
    return value
}

fun powerUnitLabel(unit: String): String {
    val key = canonicalUnit(unit)
    return if (key == "kw") "kW" else key
}
