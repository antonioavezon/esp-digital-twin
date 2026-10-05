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

  var payloadNode = document.getElementById("esp-payload");
  var payload = null;
  if (payloadNode && payloadNode.textContent.trim()) {
    try {
      payload = JSON.parse(payloadNode.textContent);
    } catch (error) {
      payload = null;
    }
  }

  var byId = {};
  if (payload && Array.isArray(payload.components)) {
    payload.components.forEach(function (component) {
      byId[component.id] = component;
    });
  }

  document.querySelectorAll("[data-component]").forEach(function (element) {
    var component = byId[element.getAttribute("data-component")];
    if (component) {
      element.setAttribute("aria-label", component.name);
    }
  });

  var empty = document.getElementById("detail-empty");
  var detail = document.getElementById("detail");

  function select(id) {
    document.querySelectorAll(".is-selected").forEach(function (element) {
      element.classList.remove("is-selected");
      element.setAttribute("aria-pressed", "false");
    });
    document.querySelectorAll('[data-component="' + id + '"]').forEach(function (element) {
      element.classList.add("is-selected");
      if (element.getAttribute("aria-pressed") !== null || element.tagName === "BUTTON") {
        element.setAttribute("aria-pressed", "true");
      }
    });

    var component = byId[id];
    if (!detail || !empty) {
      return;
    }
    if (!component) {
      empty.hidden = false;
      empty.textContent = (window.EspUi && window.EspUi.detail_missing) || "Sin datos de esp-core para este componente.";
      detail.hidden = true;
      return;
    }

    empty.hidden = true;
    detail.hidden = false;
    document.getElementById("detail-name").textContent = component.name;
    document.getElementById("detail-location").textContent = component.location_label;
    document.getElementById("detail-function").textContent = component.function;
    document.getElementById("detail-input").textContent = component.input;
    document.getElementById("detail-output").textContent = component.output;
    document.getElementById("detail-relation").textContent = component.relation;
    document.getElementById("detail-description").textContent = component.description;
    var explore = document.getElementById("detail-explore");
    if (explore) {
      explore.hidden = id !== "pump";
    }
  }

  document.body.addEventListener("click", function (event) {
    var target = event.target.closest("[data-component]");
    if (!target) {
      return;
    }
    select(target.getAttribute("data-component"));
  });

  document.body.addEventListener("keydown", function (event) {
    if (event.key !== "Enter" && event.key !== " ") {
      return;
    }
    var target = event.target.closest("[data-component]");
    if (!target || target.tagName === "BUTTON") {
      return;
    }
    event.preventDefault();
    select(target.getAttribute("data-component"));
  });

  function setFlow(buttonId, className, listId, on) {
    var button = document.getElementById(buttonId);
    var list = document.getElementById(listId);
    document.body.classList.toggle(className, on);
    if (button) {
      button.setAttribute("aria-pressed", on ? "true" : "false");
    }
    if (list) {
      list.hidden = !on;
    }
  }

  function bindToggle(buttonId, className, listId) {
    var button = document.getElementById(buttonId);
    if (!button) {
      return;
    }
    button.addEventListener("click", function () {
      var active = !document.body.classList.contains(className);
      setFlow(buttonId, className, listId, active);
    });
  }

  bindToggle("toggle-energy", "flow-energy", "energy-steps");
  bindToggle("toggle-fluid", "flow-fluid", "fluid-steps");

  var start = document.getElementById("esp-start");
  var stop = document.getElementById("esp-stop");
  var runValue = document.getElementById("esp-run-value");

  function setRunning(on) {
    document.body.classList.toggle("esp-running", on);
    if (start) {
      start.setAttribute("aria-pressed", on ? "true" : "false");
    }
    if (stop) {
      stop.setAttribute("aria-pressed", on ? "false" : "true");
    }
    if (runValue) {
      runValue.textContent = on ? runValue.getAttribute("data-on") : runValue.getAttribute("data-off");
    }
    if (on) {
      setFlow("toggle-energy", "flow-energy", "energy-steps", true);
      setFlow("toggle-fluid", "flow-fluid", "fluid-steps", true);
    }
  }

  if (start) {
    start.addEventListener("click", function () {
      setRunning(true);
    });
  }
  if (stop) {
    stop.addEventListener("click", function () {
      setRunning(false);
    });
  }
})();
