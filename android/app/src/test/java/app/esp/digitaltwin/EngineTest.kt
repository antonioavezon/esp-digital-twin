package app.esp.digitaltwin

import app.esp.digitaltwin.engine.Experiment
import app.esp.digitaltwin.engine.Experiments
import app.esp.digitaltwin.engine.HzIssue
import app.esp.digitaltwin.engine.Measured
import app.esp.digitaltwin.engine.ModelException
import app.esp.digitaltwin.engine.compareFluids
import app.esp.digitaltwin.engine.domain
import app.esp.digitaltwin.engine.formatG6
import app.esp.digitaltwin.engine.interpolate
import app.esp.digitaltwin.engine.parseCurves
import app.esp.digitaltwin.engine.parseDecimal
import app.esp.digitaltwin.engine.parseDocument
import app.esp.digitaltwin.engine.parseLabStages
import app.esp.digitaltwin.engine.parseStudyHz
import app.esp.digitaltwin.engine.presentCurve
import app.esp.digitaltwin.engine.runHydraulics
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Test

class EngineTest {
    @Test
    fun knownHydraulicCaseMatchesTheBundledModel() {
        val result = runHydraulics(
            intake = Measured(100.0, "psi"),
            discharge = Measured(300.0, "psi"),
            density = Measured(1000.0, "kg/m3"),
            flow = Measured(500.0, "m3/day"),
            stages = 1,
        )
        assertEquals("200 psi", result.deltaP.display)
        assertEquals("140.614 m", result.head.display)
        assertEquals("7.98004 kW", result.power.display)
        assertEquals("140.614 m", result.stageHead?.display)
        assertEquals(1378951.458633672, result.deltaP.siValue, 1e-6)
    }

    @Test
    fun invalidInputIsRejectedAndDoesNotInventAResult() {
        assertNull(parseDecimal("abc"))
        assertNull(parseDecimal(""))
        assertNull(parseLabStages("0"))
        assertNull(parseLabStages("121"))
        assertEquals(1, parseLabStages("1"))
        val (kept, issue) = parseStudyHz("10", 60.0)
        assertEquals(60.0, kept!!, 0.0)
        assertEquals(HzIssue.INVALID, issue)
        val (emptyKept, emptyIssue) = parseStudyHz("  ", 45.0)
        assertEquals(45.0, emptyKept!!, 0.0)
        assertEquals(HzIssue.EMPTY, emptyIssue)
        try {
            runHydraulics(Measured(-1.0, "psi"), Measured(10.0, "psi"), Measured(1000.0, "kg/m3"), Measured(1.0, "m3/day"), 1)
            fail("negative pressure must be rejected")
        } catch (exc: ModelException) {
            assertEquals("pressure_negative", exc.code)
        }
    }

    @Test
    fun includedExperimentsDifferByPressureAndDensity() {
        val base = run(Experiments.all.first { it.id == "base-water" })
        val higher = run(Experiments.all.first { it.id == "higher-differential" })
        val lighter = run(Experiments.all.first { it.id == "different-density" })
        assertEquals("200 psi", base.deltaP.display)
        assertEquals("140.614 m", base.head.display)
        assertEquals("400 psi", higher.deltaP.display)
        assertEquals(base.head.siValue * 2.0, higher.head.siValue, 1e-9)
        assertEquals(base.power.siValue * 2.0, higher.power.siValue, 1e-6)
        assertEquals(base.deltaP.siValue, lighter.deltaP.siValue, 1e-6)
        assertEquals(base.power.siValue, lighter.power.siValue, 1e-6)
        assertTrue(lighter.head.siValue > base.head.siValue)
    }

    private fun run(experiment: Experiment) = runHydraulics(
        Measured(experiment.intake, "psi"),
        Measured(experiment.discharge, "psi"),
        Measured(experiment.density, "kg/m3"),
        Measured(experiment.flow, "m3/day"),
        1,
    )

    @Test
    fun compareKeepsPressureAndChangesHead() {
        val compared = compareFluids(
            Measured(100.0, "psi"),
            Measured(300.0, "psi"),
            Measured(500.0, "m3/day"),
            listOf("Fluid A" to Measured(1000.0, "kg/m3"), "Fluid B" to Measured(850.0, "kg/m3")),
        )
        assertEquals(true, compared.samePressure)
        assertEquals(false, compared.sameHead)
        assertEquals("density", compared.lessonCode)
        assertEquals(compared.cases[0].result.deltaP.siValue, compared.cases[1].result.deltaP.siValue, 1e-6)
    }

    @Test
    fun bundledRedaCurveKeepsSheetBepAndDoesNotExtrapolate() {
        val text = javaClass.classLoader.getResourceAsStream("reda.json")?.bufferedReader()?.readText()
            ?: error("reda.json is not on the test classpath")
        val curve = parseCurves(parseDocument(text)).first { it.id == "reda-d5800n-400-60hz-3500rpm-p1" }
        val presented = presentCurve(curve, stages = 1, flowUnit = "bpd", headUnit = "ft", powerUnit = "hp")
        assertEquals("5820", formatG6(presented.bep!!.flow))
        assertEquals(22.63, presented.bep.head, 1e-9)
        assertEquals(1.38, presented.bep.shaftPower, 1e-9)
        assertEquals(70.17, presented.bep.efficiencyPercent, 1e-9)
        assertEquals(29.6564, presented.head.first().value, 1e-4)
        assertEquals("approximate_digitization", presented.warnings.first())
        assertNull(interpolate(doubleArrayOf(0.0, 1.0), doubleArrayOf(2.0, 4.0), 1.5))
        assertNull(domain(emptyList()))
        val outside = interpolate(
            curve.head.map { it.flowM3s }.toDoubleArray(),
            curve.head.map { it.valueSi }.toDoubleArray(),
            curve.head.last().flowM3s + 1.0,
        )
        assertNull(outside)
    }
}
