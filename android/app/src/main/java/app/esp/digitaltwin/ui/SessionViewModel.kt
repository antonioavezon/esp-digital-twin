package app.esp.digitaltwin.ui

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import app.esp.digitaltwin.data.LabSnapshot
import app.esp.digitaltwin.data.Preferences
import app.esp.digitaltwin.engine.CompareResult
import app.esp.digitaltwin.engine.Experiment
import app.esp.digitaltwin.engine.Experiments
import app.esp.digitaltwin.engine.HydraulicsResult
import app.esp.digitaltwin.engine.HzIssue
import app.esp.digitaltwin.engine.Measured
import app.esp.digitaltwin.engine.ModelException
import app.esp.digitaltwin.engine.formatG6
import app.esp.digitaltwin.engine.parseLabStages
import app.esp.digitaltwin.engine.parseStudyHz
import app.esp.digitaltwin.engine.runHydraulics
import kotlinx.coroutines.launch

class SessionViewModel(private val preferences: Preferences) : ViewModel() {
    var studyHz by mutableStateOf(60.0)
    var hzDraft by mutableStateOf("60")
    var hzIssue by mutableStateOf<HzIssue?>(null)
    var intake by mutableStateOf("")
    var intakeUnit by mutableStateOf("psi")
    var discharge by mutableStateOf("")
    var dischargeUnit by mutableStateOf("psi")
    var density by mutableStateOf("")
    var densityUnit by mutableStateOf("kg/m3")
    var flow by mutableStateOf("")
    var flowUnit by mutableStateOf("m3/day")
    var stages by mutableStateOf("1")
    var result by mutableStateOf<HydraulicsResult?>(null)
    var snapshot by mutableStateOf<LabSnapshot?>(null)
    var formError by mutableStateOf<String?>(null)
    var compare by mutableStateOf<CompareResult?>(null)
    var compareError by mutableStateOf<String?>(null)
    var experimentId by mutableStateOf<String?>(null)
    var chartExpanded by mutableStateOf(false)
    var fluidA by mutableStateOf(Experiments.compareA.first)
    var fluidB by mutableStateOf(Experiments.compareB.first)
    var densityA by mutableStateOf("")
    var densityB by mutableStateOf("")
    var manufacturer by mutableStateOf("")
    var series by mutableStateOf("")
    var model by mutableStateOf("")
    var speed by mutableStateOf("")
    var curveStages by mutableStateOf("")
    var curveFlowUnit by mutableStateOf("bpd")
    var curveHeadUnit by mutableStateOf("ft")
    var curvePowerUnit by mutableStateOf("hp")
    var showHead by mutableStateOf(true)
    var showPower by mutableStateOf(true)
    var showEfficiency by mutableStateOf(true)
    var curveError by mutableStateOf<String?>(null)
    var pumpPartId by mutableStateOf<String?>(null)
    var conceptualRun by mutableStateOf(false)
    var showEnergy by mutableStateOf(false)
    var showFluid by mutableStateOf(false)
    private var prefilled = false
    private var hzLoaded = false

    init {
        viewModelScope.launch {
            preferences.studyHz.collect { value ->
                if (!hzLoaded) {
                    studyHz = value
                    hzDraft = formatG6(value)
                    hzLoaded = true
                }
            }
        }
    }

    fun editHz(raw: String) {
        hzDraft = raw
        val (value, issue) = parseStudyHz(raw, studyHz)
        hzIssue = issue
        if (issue == null && value != null) {
            studyHz = value
            viewModelScope.launch { preferences.setStudyHz(value) }
        }
    }

    fun resetHz() {
        studyHz = 60.0
        hzDraft = "60"
        hzIssue = null
        viewModelScope.launch { preferences.setStudyHz(60.0) }
    }

    fun prefillIfNeeded() {
        if (prefilled) return
        prefilled = true
        val base = Experiments.all.first()
        intake = formatG6(base.intake)
        discharge = formatG6(base.discharge)
        density = formatG6(base.density)
        flow = formatG6(base.flow)
        intakeUnit = "psi"
        dischargeUnit = "psi"
        densityUnit = "kg/m3"
        flowUnit = "m3/day"
        stages = "1"
        densityA = formatG6(Experiments.compareA.second)
        densityB = formatG6(Experiments.compareB.second)
    }

    fun applyExperiment(experiment: Experiment) {
        intake = formatG6(experiment.intake)
        discharge = formatG6(experiment.discharge)
        density = formatG6(experiment.density)
        flow = formatG6(experiment.flow)
        intakeUnit = "psi"
        dischargeUnit = "psi"
        densityUnit = "kg/m3"
        flowUnit = "m3/day"
        experimentId = experiment.id
        compare = null
        compareError = null
        val stageCount = parseLabStages(stages) ?: 1.also { stages = "1" }
        try {
            val computed = runHydraulics(
                Measured(experiment.intake, intakeUnit),
                Measured(experiment.discharge, dischargeUnit),
                Measured(experiment.density, densityUnit),
                Measured(experiment.flow, flowUnit),
                stageCount,
            )
            result = computed
            snapshot = LabSnapshot(
                computed.flow.siValue,
                computed.head.siValue,
                computed.power.siValue,
                computed.density.siValue,
                stageCount,
            )
            formError = null
        } catch (exc: ModelException) {
            formError = exc.code
            result = null
            snapshot = null
        }
    }

    companion object {
        fun factory(preferences: Preferences) = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T = SessionViewModel(preferences) as T
        }
    }
}
