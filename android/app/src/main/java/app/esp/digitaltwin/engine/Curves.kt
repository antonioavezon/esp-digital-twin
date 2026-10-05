package app.esp.digitaltwin.engine

data class CurvePoint(val flowM3s: Double, val valueSi: Double)

data class RawBep(
    val origin: String,
    val flowM3s: Double,
    val headM: Double,
    val powerW: Double,
    val efficiencyPercent: Double,
)

data class RawCurve(
    val id: String,
    val manufacturer: String,
    val series: String,
    val model: String,
    val frequencyHz: Double,
    val speedRpm: Double,
    val curveBasis: String,
    val specificGravity: Double,
    val head: List<CurvePoint>,
    val shaftPower: List<CurvePoint>,
    val efficiency: List<CurvePoint>,
    val bep: RawBep?,
    val rangeName: String?,
    val rangeMinBpd: Double?,
    val rangeMaxBpd: Double?,
    val dataQuality: String,
    val digitizationWarning: String?,
    val sourceDocument: String,
    val sourcePage: String,
)

private fun series(points: List<CurvePoint>, flowUnit: String, multiplier: Double, convert: (Double) -> Double): List<Sample> =
    points.map { Sample(fromM3s(it.flowM3s, flowUnit), convert(it.valueSi * multiplier)) }

fun presentCurve(
    curve: RawCurve,
    stages: Int?,
    flowUnit: String,
    headUnit: String,
    powerUnit: String,
): PresentedCurve {
    if (stages != null && stages < 1) throw ModelException("stages")
    val perStage = curve.curveBasis == "per_stage"
    val multiplier = if (stages == null || !perStage) 1.0 else stages.toDouble()
    val basis = when {
        !perStage -> "as_published"
        stages == null -> "per_stage"
        stages == 1 -> "per_stage"
        else -> "total_estimate"
    }
    val flowKey = canonicalUnit(flowUnit)
    val headKey = canonicalUnit(headUnit)
    val powerKey = canonicalUnit(powerUnit)
    val warnings = mutableListOf<String>()
    if (curve.dataQuality == "approximate_digitization") warnings += "approximate_digitization"
    if (perStage && stages == null) warnings += "per_stage_without_count"
    val bep = curve.bep?.let {
        Bep(
            origin = it.origin,
            flow = fromM3s(it.flowM3s, flowKey),
            head = fromMetres(it.headM * multiplier, headKey),
            shaftPower = fromWatts(it.powerW * multiplier, powerKey),
            efficiencyPercent = it.efficiencyPercent,
        )
    }
    val rangeMin = curve.rangeMinBpd?.let { fromM3s(toM3s(it, "bpd"), flowKey) }
    val rangeMax = curve.rangeMaxBpd?.let { fromM3s(toM3s(it, "bpd"), flowKey) }
    return PresentedCurve(
        id = curve.id,
        manufacturer = curve.manufacturer,
        series = curve.series,
        model = curve.model,
        frequencyHz = curve.frequencyHz,
        speedRpm = curve.speedRpm,
        basisCode = basis,
        stages = if (perStage) stages else null,
        flowUnit = flowKey,
        headUnit = headKey,
        powerUnit = powerUnitLabel(powerUnit),
        head = series(curve.head, flowKey, multiplier) { fromMetres(it, headKey) },
        shaftPower = series(curve.shaftPower, flowKey, multiplier) { fromWatts(it, powerKey) },
        efficiency = series(curve.efficiency, flowKey, 1.0) { it * 100.0 },
        bep = bep,
        rangeName = curve.rangeName,
        rangeMin = rangeMin,
        rangeMax = rangeMax,
        warnings = warnings,
        digitizationWarning = curve.digitizationWarning,
        sourceDocument = curve.sourceDocument,
        sourcePage = curve.sourcePage,
        sourceQuality = curve.dataQuality,
        marker = null,
    )
}

fun withLabMarker(
    curve: RawCurve,
    presented: PresentedCurve,
    stages: Int?,
    flowM3s: Double,
    headM: Double,
    hydraulicPowerW: Double,
    densityKgM3: Double,
): PresentedCurve {
    val perStage = curve.curveBasis == "per_stage"
    val comparable = !(perStage && stages == null)
    val flowKey = presented.flowUnit
    val headKey = canonicalUnit(presented.headUnit)
    val powerKey = canonicalUnit(presented.powerUnit)
    val warnings = presented.warnings.toMutableList()
    var shaft: Double? = null
    var etaPercent: Double? = null
    var estimate: Double? = null
    if (comparable) {
        val headSi = interpolate(curve.head.map { it.flowM3s }.toDoubleArray(), curve.head.map { it.valueSi }.toDoubleArray(), flowM3s)
        val powerSi = interpolate(curve.shaftPower.map { it.flowM3s }.toDoubleArray(), curve.shaftPower.map { it.valueSi }.toDoubleArray(), flowM3s)
        val eta = interpolate(curve.efficiency.map { it.flowM3s }.toDoubleArray(), curve.efficiency.map { it.valueSi }.toDoubleArray(), flowM3s)
        val multiplier = (stages ?: 1).toDouble()
        if (headSi == null || powerSi == null || eta == null) {
            warnings += "outside_flow_range"
        } else {
            shaft = fromWatts(powerSi * multiplier, powerKey)
            etaPercent = eta * 100.0
            if (eta <= 0.0) {
                warnings += "efficiency_unavailable"
            } else {
                estimate = fromWatts(hydraulicPowerW / eta, powerKey)
            }
        }
        val reference = curve.specificGravity * 1000.0
        if (reference > 0.0 && abs(densityKgM3 - reference) / reference > 0.02) {
            warnings += "density_not_corrected"
        }
    }
    val marker = Marker(
        comparable = comparable,
        flow = if (comparable) fromM3s(flowM3s, flowKey) else null,
        head = if (comparable) fromMetres(headM, headKey) else null,
        hydraulicPower = fromWatts(hydraulicPowerW, powerKey),
        shaftFromCurve = shaft,
        efficiencyPercent = etaPercent,
        estimate = estimate,
    )
    return presented.copy(warnings = warnings, marker = marker)
}

private fun abs(value: Double) = kotlin.math.abs(value)
