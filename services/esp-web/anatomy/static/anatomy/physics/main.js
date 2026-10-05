(function () {
  "use strict";

  window.EspUi = window.EspUi || {};
  var uiNode = document.getElementById("ui-copy");
  if (uiNode && uiNode.textContent.trim()) {
    try {
      window.EspUi = JSON.parse(uiNode.textContent);
    } catch (error) {
      window.EspUi = {};
    }
  }

  var constantsNode = document.getElementById("physics-constants");
  if (!constantsNode || !constantsNode.textContent.trim() || !window.EspPhysics) {
    return;
  }
  var constants = null;
  try {
    constants = JSON.parse(constantsNode.textContent);
  } catch (error) {
    constants = null;
  }
  if (!constants || !constants.experiments) {
    return;
  }

  var experiments = {};
  constants.experiments.forEach(function (experiment) {
    experiments[experiment.id] = experiment;
  });

  function calculate() {
    var payload = window.EspPhysics.readForm();
    window.EspPhysics.showError("");
    window.EspPhysics.postJson("/physics/api/hydraulics/", payload).then(function (response) {
      if (!response.ok) {
        window.EspPhysics.showError(window.EspPhysics.errorMessage(response.data));
        return;
      }
      window.EspPhysics.paint(response.data);
      if (!document.getElementById("chart-head")) {
        return null;
      }
      return window.EspPhysics.postJson("/physics/api/charts/", payload);
    }).then(function (charts) {
      if (!charts || !charts.ok) {
        return;
      }
      window.EspPhysics.drawChart("chart-head", "chart-head-note", charts.data.head_vs_pressure);
      window.EspPhysics.drawChart("chart-power", "chart-power-note", charts.data.power_vs_flow);
    }).catch(function () {
      window.EspPhysics.showError((window.EspUi && window.EspUi.js_lab) || "No se pudo hablar con el laboratorio.");
    });
  }

  var calculateButton = document.getElementById("physics-calculate");
  if (calculateButton) {
    calculateButton.addEventListener("click", calculate);
  }

  var showButton = document.getElementById("show-calculation");
  var calcPanel = document.getElementById("calc-panel");
  if (showButton && calcPanel) {
    showButton.addEventListener("click", function () {
      var open = calcPanel.hidden;
      calcPanel.hidden = !open;
      showButton.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  document.querySelectorAll("[data-experiment]").forEach(function (button) {
    button.addEventListener("click", function () {
      var experiment = experiments[button.getAttribute("data-experiment")];
      if (!experiment) {
        return;
      }
      document.querySelectorAll("[data-experiment]").forEach(function (other) {
        other.setAttribute("aria-pressed", other === button ? "true" : "false");
      });
      window.EspPhysics.fillForm(experiment.request);
      calculate();
    });
  });

  var compareButton = document.getElementById("compare-fluids");
  if (compareButton && constants.compare_fluids) {
    compareButton.addEventListener("click", function () {
      var current = window.EspPhysics.readForm();
      var payload = {
        intake_pressure: current.intake_pressure,
        discharge_pressure: current.discharge_pressure,
        flow_rate: current.flow_rate,
        fluids: constants.compare_fluids.fluids,
      };
      window.EspPhysics.showError("");
      window.EspPhysics.postJson("/physics/api/compare/", payload).then(function (response) {
        if (!response.ok) {
          window.EspPhysics.showError(window.EspPhysics.errorMessage(response.data));
          return;
        }
        window.EspPhysics.paintCompare(response.data);
        if (response.data.cases && response.data.cases[0]) {
          window.EspPhysics.paint(response.data.cases[0].result);
        }
      }).catch(function () {
        window.EspPhysics.showError((window.EspUi && window.EspUi.js_compare) || "No se pudo comparar los fluidos.");
      });
    });
  }
})();
