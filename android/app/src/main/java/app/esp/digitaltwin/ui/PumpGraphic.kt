package app.esp.digitaltwin.ui

import android.graphics.Paint
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
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.input.pointer.pointerInput

private val Amber = Color(0xFFE0A84A)
private val Teal = Color(0xFF3CBFB6)
private val Blade = Color(0xFFE7D7B0)

@Composable
fun PumpGraphic(
    playing: Boolean,
    showFluid: Boolean,
    stages: Int,
    selected: String?,
    onSelect: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val motion = rememberInfiniteTransition(label = "pump")
    val dash by motion.animateFloat(0f, 32f, infiniteRepeatable(tween(1000, easing = LinearEasing)), label = "dash")
    val spin by motion.animateFloat(0f, 360f, infiniteRepeatable(tween(1800, easing = LinearEasing)), label = "spin")
    Canvas(
        modifier.fillMaxSize().pointerInput(stages) {
            detectTapGestures { point ->
                val layout = layoutOf(size.width.toFloat(), size.height.toFloat(), stages)
                val hit = layout.wheels.firstOrNull { point.y in it.top..it.bottom }
                if (hit != null) {
                    val localY = (point.y - hit.center.y) / layout.scale
                    onSelect(if (localY < -20f) "diffuser" else "impeller")
                }
            }
        },
    ) {
        val layout = layoutOf(size.width, size.height, stages)
        drawRect(Color(0xFF101820))
        drawRoundRect(
            Color(0xFF2C281F),
            topLeft = Offset(size.width / 2f - 70f * layout.scale, layout.motorTop),
            size = Size(140f * layout.scale, layout.motorHeight),
            cornerRadius = CornerRadius(8f, 8f),
        )
        drawCircle(Amber, 16f * layout.scale, Offset(size.width / 2f, layout.motorTop + layout.motorHeight / 2f), style = Stroke(2f))
        label(size.width / 2f, layout.motorTop + layout.motorHeight - 8f, "Motor", layout.scale)
        drawRoundRect(
            Color(0xFF1C2938),
            topLeft = Offset(size.width / 2f - 70f * layout.scale, 8f),
            size = Size(140f * layout.scale, layout.regHeight),
            cornerRadius = CornerRadius(8f, 8f),
        )
        label(size.width / 2f, 8f + layout.regHeight * 0.7f, "Regulador", layout.scale)
        layout.wheels.forEachIndexed { index, wheel ->
            val active = selected == "diffuser" || selected == "impeller" || selected == "stage-$index"
            drawRoundRect(
                Color(0xFF1A2940),
                topLeft = Offset(wheel.center.x - 70f * layout.scale, wheel.top),
                size = Size(140f * layout.scale, wheel.bottom - wheel.top),
                cornerRadius = CornerRadius(8f * layout.scale, 8f * layout.scale),
                style = Stroke(if (active) 3f else 1.5f),
            )
            val diffuserTop = wheel.top + 8f * layout.scale
            drawRoundRect(
                if (selected == "diffuser") Color.White else Color(0xFF3D5A52),
                topLeft = Offset(wheel.center.x - 52f * layout.scale, diffuserTop),
                size = Size(104f * layout.scale, 48f * layout.scale),
                cornerRadius = CornerRadius(6f * layout.scale, 6f * layout.scale),
                style = Stroke(2f),
            )
            val pivot = Offset(wheel.center.x, wheel.center.y + 28f * layout.scale)
            drawCircle(
                if (selected == "impeller") Color.White else Color(0xFF243140),
                46f * layout.scale,
                pivot,
                style = Stroke(2f),
            )
            rotate(if (playing) spin else 0f, pivot) {
                fun blade(x1: Float, y1: Float, x2: Float, y2: Float) {
                    drawLine(
                        Blade,
                        Offset(pivot.x + x1 * layout.scale, pivot.y + y1 * layout.scale),
                        Offset(pivot.x + x2 * layout.scale, pivot.y + y2 * layout.scale),
                        2.2f * layout.scale,
                    )
                }
                blade(0f, -34f, 0f, -10f)
                blade(0f, 10f, 0f, 34f)
                blade(-34f, 0f, -10f, 0f)
                blade(10f, 0f, 34f, 0f)
                blade(-24f, -24f, -8f, -8f)
                blade(8f, 8f, 24f, 24f)
                blade(24f, -24f, 8f, -8f)
                blade(-8f, 8f, -24f, 24f)
                if (showFluid) {
                    val openRight = Path().apply {
                        moveTo(pivot.x, pivot.y + 6f * layout.scale)
                        cubicTo(
                            pivot.x + 18f * layout.scale, pivot.y + 18f * layout.scale,
                            pivot.x + 32f * layout.scale, pivot.y + 8f * layout.scale,
                            pivot.x + 44f * layout.scale, pivot.y,
                        )
                    }
                    val openLeft = Path().apply {
                        moveTo(pivot.x, pivot.y - 6f * layout.scale)
                        cubicTo(
                            pivot.x - 18f * layout.scale, pivot.y - 18f * layout.scale,
                            pivot.x - 32f * layout.scale, pivot.y - 8f * layout.scale,
                            pivot.x - 44f * layout.scale, pivot.y,
                        )
                    }
                    fluid(openRight, layout.scale, playing, dash)
                    fluid(openLeft, layout.scale, playing, dash)
                }
            }
            drawCircle(Color(0xFF0C1116), 8f * layout.scale, pivot)
            drawLine(
                Color(0xFF8FB8B0),
                Offset(wheel.center.x - 40f * layout.scale, diffuserTop + 44f * layout.scale),
                Offset(wheel.center.x - 6f * layout.scale, diffuserTop + 4f),
                2f,
            )
            drawLine(
                Color(0xFF8FB8B0),
                Offset(wheel.center.x + 40f * layout.scale, diffuserTop + 44f * layout.scale),
                Offset(wheel.center.x + 6f * layout.scale, diffuserTop + 4f),
                2f,
            )
            label(wheel.center.x, wheel.top + 22f * layout.scale, "${index + 1}", layout.scale)
        }
        if (showFluid && layout.wheels.isNotEmpty()) {
            val s = layout.scale
            val cx = size.width / 2f
            val ordered = layout.wheels
            val firstEye = ordered.first().center.y + 28f * s
            fluid(
                Path().apply {
                    moveTo(cx, layout.motorTop)
                    lineTo(cx, firstEye)
                },
                s, playing, dash,
            )
            ordered.forEachIndexed { index, wheel ->
                val eye = wheel.center.y + 28f * s
                val diffuserTop = wheel.top + 8f * s
                val mouth = diffuserTop + 46f * s
                fluid(
                    Path().apply {
                        moveTo(cx - 42f * s, eye - 4f * s)
                        cubicTo(cx - 46f * s, mouth, cx - 14f * s, diffuserTop + 14f * s, cx, diffuserTop)
                    },
                    s, playing, dash,
                )
                fluid(
                    Path().apply {
                        moveTo(cx + 42f * s, eye - 4f * s)
                        cubicTo(cx + 46f * s, mouth, cx + 14f * s, diffuserTop + 14f * s, cx, diffuserTop)
                    },
                    s, playing, dash,
                )
                val nextY = if (index < ordered.lastIndex) ordered[index + 1].center.y + 28f * s else 8f + layout.regHeight
                fluid(Path().apply { moveTo(cx, diffuserTop); lineTo(cx, nextY) }, s, playing, dash)
            }
            val exitY = 8f + layout.regHeight * 0.5f
            val exitX = size.width - 8f
            fluid(
                Path().apply {
                    moveTo(cx, 8f + layout.regHeight)
                    lineTo(cx, exitY)
                    lineTo(exitX, exitY)
                },
                s, playing, dash,
            )
            label(exitX - 28f * s.coerceAtLeast(0.8f), exitY - 8f, "Salida", s.coerceAtLeast(0.9f))
        }
    }
}

private fun androidx.compose.ui.graphics.drawscope.DrawScope.fluid(path: Path, scale: Float, playing: Boolean, dash: Float) {
    drawPath(
        path,
        Teal,
        style = Stroke(
            width = 2.6f * scale,
            cap = androidx.compose.ui.graphics.StrokeCap.Round,
            pathEffect = PathEffect.dashPathEffect(
                floatArrayOf(7f * scale, 9f * scale),
                if (playing) -dash * scale else 0f,
            ),
        ),
    )
}

private data class Wheel(val center: Offset, val top: Float, val bottom: Float)
private data class Layout(
    val scale: Float,
    val wheels: List<Wheel>,
    val motorTop: Float,
    val motorHeight: Float,
    val regHeight: Float,
)

private fun layoutOf(width: Float, height: Float, stages: Int): Layout {
    val count = stages.coerceIn(1, 3)
    val regHeight = height * 0.12f
    val motorHeight = height * 0.14f
    val motorTop = height - motorHeight - 4f
    val midTop = regHeight + 12f
    val midBottom = motorTop - 8f
    val gap = (midBottom - midTop) / count
    val scale = minOf(width / 220f, gap / 160f).coerceIn(0.45f, 1.4f)
    val wheels = List(count) { index ->
        val slotFromTop = count - 1 - index
        val top = midTop + gap * slotFromTop
        Wheel(Offset(width / 2f, top + gap * 0.55f), top, top + gap - 6f)
    }
    return Layout(scale, wheels, motorTop, motorHeight, regHeight)
}

private fun androidx.compose.ui.graphics.drawscope.DrawScope.label(x: Float, y: Float, text: String, scale: Float) {
    drawContext.canvas.nativeCanvas.drawText(
        text,
        x,
        y,
        Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = android.graphics.Color.parseColor("#9AAFC3")
            textAlign = Paint.Align.CENTER
            textSize = 14f * scale
        },
    )
}
