package app.esp.digitaltwin.engine

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

private val json = Json { ignoreUnknownKeys = true }

fun JsonObject.text(key: String): String {
    val value = this[key] ?: return ""
    return (value as? JsonPrimitive)?.contentOrNull ?: ""
}

fun JsonObject.number(key: String): Double {
    val primitive = this[key]?.jsonPrimitive ?: throw ModelException("catalog")
    return primitive.doubleOrNull ?: primitive.content.toDouble()
}

fun JsonObject.optionalNumber(key: String): Double? {
    val primitive = this[key] as? JsonPrimitive ?: return null
    return primitive.doubleOrNull ?: primitive.content.toDoubleOrNull()
}

fun JsonObject.child(key: String): JsonObject? = this[key] as? JsonObject

fun JsonObject.array(key: String): JsonArray? = this[key] as? JsonArray

fun JsonObject.objects(key: String): List<JsonObject> =
    array(key)?.map { it.jsonObject } ?: emptyList()

fun parseDocument(text: String): JsonObject = json.parseToJsonElement(text).jsonObject

private fun points(array: JsonArray?): List<CurvePoint> =
    array?.map { element ->
        val point = element.jsonObject
        CurvePoint(point.number("flow_m3_s"), point.number("value_si"))
    } ?: emptyList()

fun parseCurves(document: JsonObject): List<RawCurve> =
    document.objects("curves").map { curve ->
        val bep = curve.child("bep")?.let {
            RawBep(
                origin = it.text("origin"),
                flowM3s = it.number("flow_m3_s"),
                headM = it.number("head_m"),
                powerW = it.number("power_w"),
                efficiencyPercent = it.number("efficiency_percent"),
            )
        }
        val range = curve.child("operating_range")
        RawCurve(
            id = curve.text("id"),
            manufacturer = curve.text("manufacturer"),
            series = curve.text("series"),
            model = curve.text("model"),
            frequencyHz = curve.number("frequency_hz"),
            speedRpm = curve.number("speed_rpm"),
            curveBasis = curve.text("curve_basis"),
            specificGravity = curve.optionalNumber("specific_gravity_reference") ?: 1.0,
            head = points(curve.array("head_flow_points")),
            shaftPower = points(curve.array("shaft_power_flow_points")),
            efficiency = points(curve.array("efficiency_flow_points")),
            bep = bep,
            rangeName = range?.text("name")?.ifBlank { null },
            rangeMinBpd = range?.optionalNumber("flow_min_bpd"),
            rangeMaxBpd = range?.optionalNumber("flow_max_bpd"),
            dataQuality = curve.text("data_quality"),
            digitizationWarning = curve.child("digitization")?.text("warning")?.ifBlank { null },
            sourceDocument = curve.text("source_document"),
            sourcePage = curve.text("source_page"),
        )
    }

data class BundledContent(
    val esp: JsonObject,
    val english: JsonObject,
    val pump: JsonObject,
    val sourceNote: String,
    val curves: List<RawCurve>,
)

fun parseBundled(esp: String, english: String, pump: String, reda: String): BundledContent {
    val curvesDoc = parseDocument(reda)
    return BundledContent(
        esp = parseDocument(esp),
        english = parseDocument(english),
        pump = parseDocument(pump),
        sourceNote = curvesDoc.text("source_note"),
        curves = parseCurves(curvesDoc),
    )
}
