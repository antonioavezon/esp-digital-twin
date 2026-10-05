package app.esp.digitaltwin.ui

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.input.pointer.pointerInput
import android.graphics.Paint

private val Amber = Color(0xFFE0A84A)
private val Teal = Color(0xFF3CBFB6)
private val Frame = Color(0xFF46586C)
private val Ink = Color(0xFFD5E0EA)

private data class Zone(val id: String, val label: String, val l: Float, val t: Float, val r: Float, val b: Float)

private val zones = listOf(
    Zone("reservoir", "Reservorio", 36f, 992f, 724f, 1080f),
    Zone("surface", "Superficie", 36f, 16f, 724f, 192f),
    Zone("power-supply", "Alimentación", 270f, 52f, 490f, 108f),
    Zone("vsd", "Regulador", 270f, 124f, 490f, 176f),
    Zone("well", "Pozo", 250f, 198f, 510f, 1020f),
    Zone("tubing", "Tubing", 346f, 242f, 414f, 610f),
    Zone("production-flow", "Flujo", 500f, 204f, 696f, 234f),
    Zone("electrical-cable", "Cable", 270f, 176f, 310f, 910f),
    Zone("pump", "Bomba", 305f, 614f, 455f, 702f),
    Zone("intake", "Admisión", 305f, 706f, 455f, 758f),
    Zone("protector", "Protector", 305f, 762f, 455f, 828f),
    Zone("motor", "Motor", 305f, 832f, 455f, 932f),
    Zone("shaft", "Eje", 368f, 640f, 392f, 848f),
)

@Composable
fun WellSchematic(
    running: Boolean,
    energy: Boolean,
    fluid: Boolean,
    selected: String?,
    onSelect: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val motion = rememberInfiniteTransition(label = "well")
    val dash by motion.animateFloat(0f, 34f, infiniteRepeatable(tween(900, easing = LinearEasing)), label = "dash")
    val spin by motion.animateFloat(0f, 360f, infiniteRepeatable(tween(1800, easing = LinearEasing)), label = "spin")
    Canvas(
        modifier
            .fillMaxSize()
            .pointerInput(onSelect) {
                detectTapGestures { point ->
                    val s = minOf(size.width / 760f, size.height / 1100f)
                    val ox = (size.width - 760f * s) / 2f
                    val oy = (size.height - 1100f * s) / 2f
                    val x = (point.x - ox) / s
                    val y = (point.y - oy) / s
                    zones.asReversed().firstOrNull { x in it.l..it.r && y in it.t..it.b }?.let { onSelect(it.id) }
                }
            },
    ) {
        val s = minOf(size.width / 760f, size.height / 1100f)
        val ox = (size.width - 760f * s) / 2f
        val oy = (size.height - 1100f * s) / 2f
        val mapX: (Float) -> Float = { v -> ox + v * s }
        val mapY: (Float) -> Float = { v -> oy + v * s }
        drawRect(Color(0xFF101820), size = size)
        fun box(zone: Zone, fill: Color) {
            val stroke = when {
                selected == zone.id -> Color.White
                energy && zone.id in energyIds -> Amber
                fluid && zone.id in fluidIds -> Teal
                else -> Frame
            }
            drawRoundRect(
                fill,
                topLeft = Offset(mapX(zone.l), mapY(zone.t)),
                size = Size((zone.r - zone.l) * s, (zone.b - zone.t) * s),
                cornerRadius = CornerRadius(4f * s, 4f * s),
            )
            drawRoundRect(
                stroke,
                topLeft = Offset(mapX(zone.l), mapY(zone.t)),
                size = Size((zone.r - zone.l) * s, (zone.b - zone.t) * s),
                cornerRadius = CornerRadius(4f * s, 4f * s),
                style = Stroke(width = if (selected == zone.id) 3f * s else 1.6f * s),
            )
        }
        box(zones[0], Color(0xFF1B1713))
        box(zones[1], Color(0xFF172230))
        drawRect(Color(0xFF243028), topLeft = Offset(mapX(36f), mapY(230f)), size = Size(688f * s, 12f * s))
        box(zones[2], Color(0xFF1C2938))
        box(zones[3], Color(0xFF1C2938))
        box(zones[4], Color(0xFF101820))
        box(zones[5], Color(0xFF182838))
        box(zones[6], Color(0xFF173238))
        box(zones[8], Color(0xFF1A2940))
        box(zones[9], Color(0xFF173036))
        box(zones[10], Color(0xFF243028))
        box(zones[11], Color(0xFF2C281F))
        val cable = linePath(mapX, mapY, 380f, 176f, 286f, 220f, 286f, 900f, 336f, 900f)
        drawPath(cable, if (energy) Amber else Color(0xFF8D7040), style = Stroke(3.5f * s, cap = androidx.compose.ui.graphics.StrokeCap.Round))
        val shaft = linePath(mapX, mapY, 380f, 848f, 380f, 640f)
        drawPath(shaft, if (energy) Amber else Color(0xFFCBB892), style = Stroke(3f * s, cap = androidx.compose.ui.graphics.StrokeCap.Round))
        flowing(this, cable, Amber, energy, running, dash, s)
        flowing(this, shaft, Amber, energy, running, dash, s)
        val fluidPath = linePath(mapX, mapY, 420f, 1048f, 470f, 1000f, 470f, 732f, 380f, 732f, 380f, 214f, 680f, 219f)
        flowing(this, fluidPath, Teal, fluid, running, -dash, s)
        val pivot = Offset(mapX(380f), mapY(652f))
        rotate(if (running) spin else 0f, pivot) {
            fun blade(x1: Float, y1: Float, x2: Float, y2: Float) {
                drawLine(Ink, Offset(pivot.x + x1 * s, pivot.y + y1 * s), Offset(pivot.x + x2 * s, pivot.y + y2 * s), 1.6f * s)
            }
            blade(-18f, 0f, 18f, 0f)
            blade(0f, -18f, 0f, 18f)
            blade(-13f, -13f, 13f, 13f)
            blade(-13f, 13f, 13f, -13f)
            drawCircle(Ink, 5f * s, pivot, style = Stroke(1.4f * s))
        }
        box(zones[3], Color(0xFF1C2938))
        box(zones[11], Color(0xFF2C281F))
        drawCircle(Color(0xFFE0A84A), 22f * s, Offset(mapX(380f), mapY(882f)), style = Stroke(2.4f * s))
        tag(mapX(380f), mapY(155f), "Regulador", 2.6f)
        tag(mapX(380f), mapY(900f), "Motor", 2.6f)
        zones.filter { it.id != "vsd" && it.id != "motor" && it.id != "well" }.forEach {
            tag(mapX((it.l + it.r) / 2f), mapY(it.t + 18f), it.label, s)
        }
    }
}

private val energyIds = setOf("power-supply", "vsd", "electrical-cable", "motor", "shaft", "pump", "surface")
private val fluidIds = setOf("reservoir", "well", "intake", "pump", "tubing", "production-flow", "surface")

private fun linePath(x: (Float) -> Float, y: (Float) -> Float, vararg coords: Float): Path {
    val path = Path()
    path.moveTo(x(coords[0]), y(coords[1]))
    var i = 2
    while (i < coords.size) {
        path.lineTo(x(coords[i]), y(coords[i + 1]))
        i += 2
    }
    return path
}

private fun flowing(scope: DrawScope, path: Path, color: Color, enabled: Boolean, running: Boolean, dash: Float, s: Float) {
    scope.drawPath(
        path,
        color.copy(alpha = if (enabled) 1f else 0.22f),
        style = Stroke(
            width = 2.6f * s,
            cap = androidx.compose.ui.graphics.StrokeCap.Round,
            pathEffect = PathEffect.dashPathEffect(floatArrayOf(7f * s, 10f * s), if (enabled && running) dash * s else 0f),
        ),
    )
}

private fun DrawScope.tag(x: Float, y: Float, text: String, s: Float) {
    drawContext.canvas.nativeCanvas.drawText(
        text,
        x,
        y,
        Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = android.graphics.Color.parseColor("#9AAFC3")
            textAlign = Paint.Align.CENTER
            textSize = 11f * s.coerceAtLeast(0.7f)
        },
    )
}
