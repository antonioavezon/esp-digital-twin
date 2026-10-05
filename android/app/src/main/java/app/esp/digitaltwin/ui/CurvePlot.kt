package app.esp.digitaltwin.ui

import android.graphics.Paint
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import app.esp.digitaltwin.engine.PresentedCurve
import app.esp.digitaltwin.engine.Sample
import app.esp.digitaltwin.engine.domain
import app.esp.digitaltwin.engine.formatG6
import kotlin.math.min

private val HeadColor = Color(0xFFE0A84A)
private val PowerColor = Color(0xFFD28B8B)
private val EffColor = Color(0xFF3CBFB6)

@Composable
fun CurvePlot(
    curve: PresentedCurve,
    showHead: Boolean,
    showPower: Boolean,
    showEfficiency: Boolean,
    quarterTurns: Int,
    flip: Boolean,
    modifier: Modifier = Modifier,
) {
    Canvas(modifier.fillMaxSize()) {
        drawRect(Color(0xFF101820))
        val label = min(size.width, size.height) * 0.055f
        val text = label.coerceIn(20f, 42f)
        val left = text * 4.2f
        val top = text * 1.6f
        val rightGap = text * 5.6f
        val bottom = text * 2.2f
        val plotW = (size.width - left - rightGap).coerceAtLeast(1f)
        val plotH = (size.height - top - bottom).coerceAtLeast(1f)
        drawRect(Color(0xFF1B2632), topLeft = Offset(left, top), size = Size(plotW, plotH))
        val flows = buildList {
            if (showHead) addAll(curve.head.map { it.flow })
            if (showPower) addAll(curve.shaftPower.map { it.flow })
            if (showEfficiency) addAll(curve.efficiency.map { it.flow })
        }
        val xDomain = domain(flows) ?: return@Canvas
        fun xOf(flow: Double) = left + ((flow - xDomain.start) / (xDomain.endInclusive - xDomain.start)).toFloat() * plotW
        fun yOf(value: Double, span: ClosedFloatingPointRange<Double>) =
            top + plotH - ((value - span.start) / (span.endInclusive - span.start)).toFloat() * plotH
        val rangeMin = curve.rangeMin
        val rangeMax = curve.rangeMax
        if (rangeMin != null && rangeMax != null) {
            val x1 = xOf(rangeMin).coerceIn(left, left + plotW)
            val x2 = xOf(rangeMax).coerceIn(left, left + plotW)
            drawRect(HeadColor.copy(alpha = 0.16f), Offset(x1, top), Size((x2 - x1).coerceAtLeast(1f), plotH))
        }
        fun stroke(samples: List<Sample>, color: Color, dash: FloatArray?, title: String, slot: Int) {
            val span = domain(samples.map { it.value }) ?: return
            val path = Path()
            samples.forEachIndexed { index, sample ->
                val p = Offset(xOf(sample.flow), yOf(sample.value, span))
                if (index == 0) path.moveTo(p.x, p.y) else path.lineTo(p.x, p.y)
            }
            drawPath(
                path,
                color,
                style = Stroke(
                    width = (text * 0.09f).coerceIn(2.4f, 5f),
                    pathEffect = dash?.let { PathEffect.dashPathEffect(floatArrayOf(it[0], it[1])) },
                ),
            )
            val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                this.color = color.toArgb()
                textSize = text
                textAlign = if (slot == 0) Paint.Align.RIGHT else Paint.Align.LEFT
            }
            val axisX = when (slot) {
                0 -> left - text * 0.35f
                1 -> left + plotW + text * 0.4f
                else -> left + plotW + text * 2.8f
            }
            drawContext.canvas.nativeCanvas.drawText(title, axisX, top + text, paint)
            drawContext.canvas.nativeCanvas.drawText(formatG6(span.endInclusive), axisX, top + text * 2.3f, paint)
            drawContext.canvas.nativeCanvas.drawText(formatG6(span.start), axisX, top + plotH, paint)
        }
        if (showHead) stroke(curve.head, HeadColor, null, curve.headUnit, 0)
        if (showPower) stroke(curve.shaftPower, PowerColor, floatArrayOf(18f, 10f), curve.powerUnit, 1)
        if (showEfficiency) stroke(curve.efficiency, EffColor, floatArrayOf(6f, 8f), "%", 2)
        curve.bep?.let { bep ->
            val x = xOf(bep.flow)
            drawLine(Color.White, Offset(x, top), Offset(x, top + plotH), (text * 0.08f).coerceIn(2f, 4f))
            val mark = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = android.graphics.Color.WHITE
                textSize = text
                textAlign = Paint.Align.CENTER
            }
            drawContext.canvas.nativeCanvas.drawText("BEP", x, top - text * 0.25f, mark)
            fun dot(value: Double, samples: List<Sample>, color: Color) {
                val span = domain(samples.map { it.value }) ?: return
                val p = Offset(x, yOf(value, span))
                drawCircle(Color.White, text * 0.28f, p)
                drawCircle(color, text * 0.16f, p)
            }
            if (showHead) dot(bep.head, curve.head, HeadColor)
            if (showPower) dot(bep.shaftPower, curve.shaftPower, PowerColor)
            if (showEfficiency) dot(bep.efficiencyPercent, curve.efficiency, EffColor)
        }
        curve.marker?.takeIf { it.comparable && it.flow != null && it.head != null && showHead }?.let { marker ->
            val span = domain(curve.head.map { it.value }) ?: return@let
            drawCircle(Color.White, text * 0.2f, Offset(xOf(marker.flow!!), yOf(marker.head!!, span)))
        }
        val axis = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = android.graphics.Color.WHITE
            textSize = text
            textAlign = Paint.Align.CENTER
        }
        val baseY = top + plotH + text * 1.35f
        drawContext.canvas.nativeCanvas.drawText(curve.flowUnit, left + plotW / 2f, baseY, axis)
        drawContext.canvas.nativeCanvas.drawText(formatG6(xDomain.start), left, baseY, axis)
        drawContext.canvas.nativeCanvas.drawText(formatG6(xDomain.endInclusive), left + plotW, baseY, axis)
    }
}
