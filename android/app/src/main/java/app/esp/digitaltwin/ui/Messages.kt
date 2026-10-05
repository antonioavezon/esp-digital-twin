package app.esp.digitaltwin.ui

import androidx.compose.runtime.Composable
import androidx.compose.ui.res.stringResource
import app.esp.digitaltwin.R

@Composable
fun modelMessage(code: String?): String? {
    if (code.isNullOrBlank()) return null
    val id = when (code) {
        "pressure_negative" -> R.string.err_pressure_negative
        "pressure_unit" -> R.string.err_pressure_unit
        "density_unit" -> R.string.err_density_unit
        "density_positive" -> R.string.err_density_positive
        "flow_negative" -> R.string.err_flow_negative
        "flow_unit" -> R.string.err_flow_unit
        "stages" -> R.string.err_stages
        "head_unit" -> R.string.err_head_unit
        "power_unit" -> R.string.err_power_unit
        "name" -> R.string.err_name
        "number" -> R.string.err_number
        "invalid_number" -> R.string.err_number
        else -> null
    }
    return if (id == null) code else stringResource(id)
}

@Composable
fun warningMessage(code: String): String = when (code) {
    "discharge_not_above_intake" -> stringResource(R.string.warn_discharge)
    "zero_flow" -> stringResource(R.string.warn_zero_flow)
    "per_stage_without_count" -> stringResource(R.string.warn_per_stage)
    "outside_flow_range" -> stringResource(R.string.warn_outside)
    "efficiency_unavailable" -> stringResource(R.string.warn_efficiency)
    "density_not_corrected" -> stringResource(R.string.warn_density)
    "approximate_digitization" -> stringResource(R.string.warn_digitized)
    else -> code
}

@Composable
fun lessonMessage(code: String): String = when (code) {
    "density" -> stringResource(R.string.lesson_density)
    "same" -> stringResource(R.string.lesson_same)
    else -> stringResource(R.string.lesson_pressure)
}

@Composable
fun stepTitle(code: String): String = when (code) {
    "delta" -> stringResource(R.string.step_delta)
    "head" -> stringResource(R.string.step_head)
    "power" -> stringResource(R.string.step_power)
    else -> stringResource(R.string.step_stage)
}

@Composable
fun stepMeaning(code: String): String = when (code) {
    "delta" -> stringResource(R.string.interp_delta)
    "head" -> stringResource(R.string.interp_head)
    "power" -> stringResource(R.string.interp_power)
    else -> stringResource(R.string.interp_stage)
}
