(function () {
  "use strict";

  window.EspPhysics = window.EspPhysics || {};

  function numberValue(id) {
    var node = document.getElementById(id);
    return node ? node.value.trim() : "";
  }

  function unitValue(id) {
    var node = document.getElementById(id);
    return node ? node.value : "";
  }

  window.EspPhysics.readForm = function () {
    var stages = numberValue("stages-value");
    var body = {
      intake_pressure: { value: Number(numberValue("intake-value")), unit: unitValue("intake-unit") },
      discharge_pressure: { value: Number(numberValue("discharge-value")), unit: unitValue("discharge-unit") },
      density: { value: Number(numberValue("density-value")), unit: unitValue("density-unit") },
      flow_rate: { value: Number(numberValue("flow-value")), unit: unitValue("flow-unit") },
    };
    if (stages !== "") {
      body.stages = Number(stages);
    }
    return body;
  };

  function assignField(id, value) {
    var node = document.getElementById(id);
    if (!node) {
      return;
    }
    var next = String(value);
    var numeric = node.type !== "select-one" && node.value !== "" && next !== "";
    var changed = numeric ? Number(node.value) !== Number(next) : node.value !== next;
    node.value = next;
    node.classList.toggle("is-changed", changed);
  }

  window.EspPhysics.fillForm = function (request) {
    assignField("intake-value", request.intake_pressure.value);
    assignField("intake-unit", request.intake_pressure.unit);
    assignField("discharge-value", request.discharge_pressure.value);
    assignField("discharge-unit", request.discharge_pressure.unit);
    assignField("density-value", request.density.value);
    assignField("density-unit", request.density.unit);
    assignField("flow-value", request.flow_rate.value);
    assignField("flow-unit", request.flow_rate.unit);
  };

  window.EspPhysics.postJson = function (url, payload) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(payload),
    }).then(function (response) {
      return response.json().then(function (data) {
        return { ok: response.ok, status: response.status, data: data };
      });
    });
  };
})();
