(function () {
  "use strict";

  window.EspPhysics = window.EspPhysics || {};

  function phrase(key, fallback) {
    return (window.EspUi && window.EspUi[key]) || fallback;
  }

  function text(id, value) {
    var node = document.getElementById(id);
    if (node) {
      node.textContent = value;
    }
  }

  window.EspPhysics.showError = function (message) {
    var node = document.getElementById("result-error");
    if (!node) {
      return;
    }
    if (!message) {
      node.hidden = true;
      node.textContent = "";
      return;
    }
    node.hidden = false;
    node.textContent = message;
  };

  window.EspPhysics.errorMessage = function (body) {
    if (!body) {
      return phrase("js_calc", "No se pudo calcular.");
    }
    var detail = body.detail && !Array.isArray(body.detail) ? body.detail : body;
    var messages = detail.messages || body.messages;
    if (messages && messages.length) {
      return messages.map(function (item) { return item.message; }).join(" ");
    }
    if (Array.isArray(body.detail)) {
      return body.detail.map(function (item) {
        var where = item.loc ? item.loc.join(".") + ": " : "";
        return where + (item.msg || "");
      }).join(" ");
    }
    return phrase("js_invalid", "La entrada no es válida.");
  };

  window.EspPhysics.paint = function (payload) {
    window.EspPhysics.lastResult = payload;
    try {
      sessionStorage.setItem("esp-lab-result", JSON.stringify(payload));
    } catch (error) {
      /* La vista Curvas puede abrirse sin este punto. */
    }
    document.dispatchEvent(new CustomEvent("esp-lab-result"));
    var results = payload.results;
    var inputs = payload.inputs;
    text("out-dp", results.pressure_difference.display);
    text("out-head", results.head.display);
    text("out-power", results.hydraulic_power.display);
    text("out-flow", results.flow_rate.display);
    text("out-g", payload.constants.gravity.display);
    text("vis-intake", inputs.intake_pressure.display);
    text("vis-discharge", inputs.discharge_pressure.display);
    text("vis-dp", "ΔP " + results.pressure_difference.display);
    text("vis-head", "Head " + results.head.display);
    text("vis-flow", "Q " + results.flow_rate.display);
    text("result-hint", payload.physics_model + " · " + payload.mode);
    text("head-meters", results.head.display);
    var shaft = document.getElementById("head-shaft");
    if (shaft) {
      var meters = Number(results.head.si_value);
      var span = 0.28;
      if (isFinite(meters) && meters > 0) {
        span = Math.max(0.28, Math.min(0.72, meters / 450));
      }
      shaft.style.height = Math.round(span * 100) + "%";
    }

    var stage = results.stage_head;
    var stageNote = document.getElementById("stage-note");
    if (stage) {
      text("out-stage", stage.display);
      if (stageNote) {
        stageNote.hidden = false;
        stageNote.textContent = stage.assumption;
      }
    } else {
      text("out-stage", "—");
      if (stageNote) {
        stageNote.hidden = true;
        stageNote.textContent = "";
      }
    }

    var warnings = document.getElementById("result-warnings");
    if (warnings) {
      warnings.replaceChildren();
      (payload.warnings || []).forEach(function (warning) {
        var item = document.createElement("li");
        item.textContent = warning.message;
        warnings.appendChild(item);
      });
    }

    var steps = document.getElementById("calc-steps");
    if (!steps) {
      return;
    }
    steps.replaceChildren();
    payload.calculation_steps.forEach(function (step) {
      var item = document.createElement("li");
      var lines = [
        "STEP " + step.order + " — " + step.title,
        step.equation,
        step.substitution,
        step.display,
        step.interpretation,
      ];
      if (step.equivalence) {
        lines.push(step.equivalence.equation);
        lines.push(step.equivalence.substitution);
        lines.push(step.equivalence.display);
      }
      item.textContent = lines.join("\n");
      steps.appendChild(item);
    });
  };

  window.EspPhysics.paintCompare = function (payload) {
    var panel = document.getElementById("compare-panel");
    if (panel) {
      panel.hidden = false;
    }
    text("compare-lesson", payload.lesson);
    var host = document.getElementById("compare-cases");
    if (!host) {
      return;
    }
    host.replaceChildren();
    payload.cases.forEach(function (item) {
      var card = document.createElement("article");
      var title = document.createElement("h3");
      title.textContent = item.name;
      var pressure = document.createElement("p");
      pressure.textContent = "ΔP " + item.result.results.pressure_difference.display;
      var head = document.createElement("p");
      head.textContent = "Head " + item.result.results.head.display;
      var density = document.createElement("p");
      density.textContent = "ρ " + item.result.inputs.density.display;
      card.append(title, pressure, head, density);
      host.appendChild(card);
    });
  };
})();
