(function () {
  "use strict";

  window.EspPump = window.EspPump || {};

  function text(id, value) {
    var node = document.getElementById(id);
    if (node) {
      node.textContent = value;
    }
  }

  window.EspPump.navigation = function (root, payload) {
    var steps = payload.flow_path.multistage.steps;
    var stages = payload.stages;
    var stageById = {};
    stages.forEach(function (stage) {
      stageById[stage.id] = stage;
    });
    var index = 0;
    var selectedPart = null;

    function stageForStep(step) {
      if (step.kind === "stage" && stageById[step.id]) {
        return stageById[step.id];
      }
      if (step.id === "discharge") {
        return stages[stages.length - 1];
      }
      return stages[0];
    }

    function partOf(stage, type) {
      var found = null;
      stage.components.forEach(function (component) {
        if (component.type === type) {
          found = component;
        }
      });
      return found;
    }

    function render() {
      var step = steps[index];
      var stage = stageForStep(step);
      var impeller = partOf(stage, "impeller");
      var diffuser = partOf(stage, "diffuser");

      root.querySelectorAll("[data-stage]").forEach(function (element) {
        var on = element.getAttribute("data-stage") === stage.id;
        element.classList.toggle("is-selected", on);
        if (element.classList.contains("stage-jump")) {
          element.classList.toggle("is-current", on);
        }
      });
      root.querySelectorAll("[data-part]").forEach(function (element) {
        var stageId = element.getAttribute("data-stage");
        var sameStage = !stageId || stageId === stage.id;
        element.classList.toggle(
          "is-selected",
          sameStage && selectedPart === element.getAttribute("data-part")
        );
      });

      text("step-label", step.label);
      text("step-summary", step.summary);
      text("stage-name", stage.name);
      text("stage-inlet", stage.inlet);
      text("stage-outlet", stage.outlet);
      text("stage-next", stage.next_label);
      if (impeller) {
        text("svg-impeller-motion", impeller.motion_label);
      }
      if (diffuser) {
        text("svg-diffuser-motion", diffuser.motion_label);
      }

      var empty = document.getElementById("part-empty");
      var panel = document.getElementById("part-detail");
      var crumb = document.getElementById("crumb-part");
      if (!selectedPart || !panel || !empty) {
        if (empty) {
          empty.hidden = false;
        }
        if (panel) {
          panel.hidden = true;
        }
        if (crumb) {
          crumb.textContent = "STAGES";
        }
      } else {
        var part = selectedPart === "diffuser" ? diffuser : impeller;
        empty.hidden = true;
        panel.hidden = false;
        text("part-name", part.name);
        text("part-motion", part.motion_label);
        text("part-simple", part.simple_explanation);
        text("part-technical", part.technical_explanation);
        text("part-receives", part.receives);
        text("part-delivers", part.delivers);
        if (crumb) {
          crumb.textContent = selectedPart === "diffuser" ? "DIFFUSER" : "IMPELLER";
        }
      }

      root.querySelectorAll(".energy-mark").forEach(function (element) {
        var order = Number(element.getAttribute("data-order"));
        element.classList.toggle("is-reached", order <= step.order);
      });

      var previous = document.getElementById("pump-prev");
      var next = document.getElementById("pump-next");
      if (previous) {
        previous.disabled = index === 0;
      }
      if (next) {
        next.disabled = index === steps.length - 1;
      }
    }

    function goToId(id) {
      var found = -1;
      steps.forEach(function (step, position) {
        if (step.id === id) {
          found = position;
        }
      });
      if (found >= 0) {
        index = found;
        render();
      }
    }

    var previous = document.getElementById("pump-prev");
    var next = document.getElementById("pump-next");
    if (previous) {
      previous.addEventListener("click", function () {
        if (index > 0) {
          index -= 1;
          render();
        }
      });
    }
    if (next) {
      next.addEventListener("click", function () {
        if (index < steps.length - 1) {
          index += 1;
          render();
        }
      });
    }

    root.querySelectorAll("[data-stage-jump]").forEach(function (button) {
      button.addEventListener("click", function () {
        goToId(button.getAttribute("data-stage-jump"));
      });
    });

    root.addEventListener("click", function (event) {
      var partElement = event.target.closest("[data-part]");
      if (partElement && root.contains(partElement)) {
        selectedPart = partElement.getAttribute("data-part");
        var stageId = partElement.getAttribute("data-stage");
        if (!stageId) {
          var current = steps[index];
          if (current.kind === "stage") {
            stageId = current.id;
          } else if (current.id === "discharge") {
            stageId = stages[stages.length - 1].id;
          } else {
            stageId = stages[0].id;
          }
        }
        goToId(stageId);
        return;
      }
      var card = event.target.closest("[data-stage-card]");
      if (card && root.contains(card)) {
        goToId(card.getAttribute("data-stage"));
      }
    });

    root.querySelectorAll("[data-view]").forEach(function (button) {
      button.addEventListener("click", function () {
        var mode = button.getAttribute("data-view");
        root.classList.toggle("view-multi", mode === "multi");
        root.classList.toggle("view-single", mode === "single");
        root.querySelectorAll("[data-view]").forEach(function (other) {
          other.setAttribute("aria-pressed", other === button ? "true" : "false");
        });
      });
    });

    root.classList.add("view-single");
    render();
  };
})();
