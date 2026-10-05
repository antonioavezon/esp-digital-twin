(function () {
  "use strict";

  var plot = document.getElementById("pump-curve-plot");
  if (!plot) {
    return;
  }

  var ui = window.EspUi || {};
  var curveCopy = document.getElementById("curve-copy");
  if (curveCopy && curveCopy.textContent.trim()) {
    try {
      var extra = JSON.parse(curveCopy.textContent);
      Object.keys(extra).forEach(function (key) {
        ui[key] = extra[key];
      });
    } catch (error) {
      extra = null;
    }
  }
  var catalog = [];
  var current = null;
  var ns = "http://www.w3.org/2000/svg";

  function phrase(key, fallback) {
    return ui[key] || fallback;
  }

  function getJson(url) {
    return fetch(url, { headers: { Accept: "application/json" } }).then(function (response) {
      return response.json().then(function (data) {
        return { ok: response.ok, data: data };
      });
    });
  }

  function postJson(url, payload) {
    if (window.EspPhysics && window.EspPhysics.postJson) {
      return window.EspPhysics.postJson(url, payload);
    }
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload),
    }).then(function (response) {
      return response.json().then(function (data) {
        return { ok: response.ok, data: data };
      });
    });
  }

  function unique(values) {
    var seen = {};
    var out = [];
    values.forEach(function (value) {
      if (!seen[value]) {
        seen[value] = true;
        out.push(value);
      }
    });
    return out;
  }

  function fillSelect(select, values, labelOf) {
    var previous = select.value;
    select.replaceChildren();
    values.forEach(function (value) {
      var option = document.createElement("option");
      option.value = value;
      option.textContent = labelOf ? labelOf(value) : value;
      select.appendChild(option);
    });
    if (values.indexOf(previous) >= 0) {
      select.value = previous;
    }
  }

  function selectedCurves() {
    var manufacturer = document.getElementById("curve-manufacturer").value;
    var series = document.getElementById("curve-series").value;
    var model = document.getElementById("curve-model").value;
    return catalog.filter(function (curve) {
      return curve.manufacturer === manufacturer && curve.series === series && curve.model === model;
    });
  }

  function refreshSelectors() {
    var manufacturer = document.getElementById("curve-manufacturer");
    var series = document.getElementById("curve-series");
    var model = document.getElementById("curve-model");
    var speed = document.getElementById("curve-speed");
    fillSelect(manufacturer, unique(catalog.map(function (curve) { return curve.manufacturer; })));
    var seriesValues = unique(catalog.filter(function (curve) {
      return curve.manufacturer === manufacturer.value;
    }).map(function (curve) { return curve.series; }));
    fillSelect(series, seriesValues);
    var modelValues = unique(catalog.filter(function (curve) {
      return curve.manufacturer === manufacturer.value && curve.series === series.value;
    }).map(function (curve) { return curve.model; }));
    fillSelect(model, modelValues);
    var speeds = selectedCurves();
    fillSelect(speed, speeds.map(function (curve) { return curve.id; }), function (id) {
      var curve = speeds.filter(function (item) { return item.id === id; })[0];
      return curve.frequency_hz + " Hz / " + curve.speed_rpm + " rpm";
    });
  }

  function query() {
    var params = new URLSearchParams();
    var stages = document.getElementById("curve-stages").value.trim();
    if (stages) {
      params.set("stages", stages);
    }
    params.set("flow_unit", document.getElementById("curve-flow-unit").value);
    params.set("head_unit", document.getElementById("curve-head-unit").value);
    params.set("power_unit", document.getElementById("curve-power-unit").value);
    return params.toString();
  }

  function checkedCount() {
    return ["show-head", "show-power", "show-eff"].filter(function (id) {
      return document.getElementById(id).checked;
    }).length;
  }

  function updateCount() {
    document.getElementById("curve-count").textContent = checkedCount() + " " + phrase("curve_of", "de") + " 3";
  }

  function svgEl(name, attrs) {
    var node = document.createElementNS(ns, name);
    Object.keys(attrs).forEach(function (key) {
      node.setAttribute(key, attrs[key]);
    });
    return node;
  }

  function extent(points, key) {
    var values = points.map(function (point) { return point[key]; });
    var min = Math.min.apply(null, values);
    var max = Math.max.apply(null, values);
    if (min === max) {
      max = min + 1;
    }
    return { min: min, max: max };
  }

  function mapRange(value, from, toStart, toSpan, invert) {
    var ratio = (value - from.min) / (from.max - from.min);
    if (invert) {
      ratio = 1 - ratio;
    }
    return toStart + ratio * toSpan;
  }

  function draw() {
    updateCount();
    plot.replaceChildren();
    if (!current || !current.series) {
      return;
    }
    var show = {
      head: document.getElementById("show-head").checked,
      shaft_power: document.getElementById("show-power").checked,
      efficiency: document.getElementById("show-eff").checked,
    };
    var styles = {
      head: { color: "#e0a84a", dash: "", name: phrase("curve_head", "Head") },
      shaft_power: { color: "#d28b8b", dash: "7 4", name: phrase("curve_power", "Shaft Power") },
      efficiency: { color: "#3cbfb6", dash: "2 3", name: phrase("curve_eff", "Efficiency") },
    };
    var units = current.display_units;
    var active = ["head", "shaft_power", "efficiency"].filter(function (key) {
      return show[key] && current.series[key] && current.series[key].length;
    });
    var left = 72;
    var top = 36;
    var width = 500;
    var height = 360;
    var flows = [];
    active.forEach(function (key) {
      current.series[key].forEach(function (point) { flows.push(point.flow); });
    });
    if (!flows.length) {
      return;
    }
    var xExtent = { min: Math.min.apply(null, flows), max: Math.max.apply(null, flows) };
    plot.appendChild(svgEl("rect", { x: left, y: top, width: width, height: height, class: "curve-frame" }));
    if (current.operating_range) {
      var range = current.operating_range;
      var x1 = mapRange(range.flow_min, xExtent, left, width, false);
      var x2 = mapRange(range.flow_max, xExtent, left, width, false);
      plot.appendChild(svgEl("rect", {
        x: Math.min(x1, x2),
        y: top,
        width: Math.abs(x2 - x1),
        height: height,
        class: "curve-range",
      }));
      plot.appendChild(svgEl("text", {
        x: (x1 + x2) / 2,
        y: top + 16,
        class: "curve-range-label",
        "text-anchor": "middle",
      })).textContent = range.name;
    }
    var slots = { head: left, shaft_power: left + width + 16, efficiency: left + width + 168 };
    active.forEach(function (key) {
      var yExtent = extent(current.series[key], "value");
      var axis = slots[key];
      var index = key === "head" ? 0 : 1;
      for (var step = 0; step <= 4; step += 1) {
        var value = yExtent.min + (yExtent.max - yExtent.min) * step / 4;
        var y = mapRange(value, yExtent, top, height, true);
        if (key === (show.head ? "head" : active[0])) {
          plot.appendChild(svgEl("line", { x1: left, x2: left + width, y1: y, y2: y, class: "curve-grid" }));
        }
        var label = svgEl("text", {
          x: index === 0 ? axis - 8 : axis + 8,
          y: y + 4,
          class: "curve-tick",
          fill: styles[key].color,
          "text-anchor": index === 0 ? "end" : "start",
        });
        label.textContent = value.toFixed(value >= 100 ? 0 : 1);
        plot.appendChild(label);
      }
      var title = svgEl("text", {
        x: index === 0 ? left : axis,
        y: 18,
        class: "curve-axis-title",
        fill: styles[key].color,
      });
      var unit = key === "head" ? units.head : (key === "shaft_power" ? units.power : units.efficiency);
      title.textContent = styles[key].name + " (" + unit + ")";
      plot.appendChild(title);
      var coords = current.series[key].map(function (point) {
        var x = mapRange(point.flow, xExtent, left, width, false);
        var y = mapRange(point.value, yExtent, top, height, true);
        return x.toFixed(1) + "," + y.toFixed(1);
      });
      plot.appendChild(svgEl("polyline", {
        points: coords.join(" "),
        fill: "none",
        stroke: styles[key].color,
        "stroke-width": "2.2",
        "stroke-dasharray": styles[key].dash,
      }));
      current.series[key]._yExtent = yExtent;
    });
    var xTitle = svgEl("text", { x: left + width / 2, y: 448, class: "curve-axis-title curve-x-title", "text-anchor": "middle" });
    xTitle.textContent = phrase("curve_flow_unit", "Flow Rate") + " (" + units.flow + ")";
    plot.appendChild(xTitle);
    if (current.bep) {
      var bx = mapRange(current.bep.flow, xExtent, left, width, false);
      plot.appendChild(svgEl("line", { x1: bx, x2: bx, y1: top, y2: top + height, class: "curve-bep-line" }));
      var bepLabel = svgEl("text", { x: bx + 4, y: top + height - 8, class: "curve-bep-label" });
      bepLabel.textContent = phrase("curve_bep_sheet", "BEP");
      plot.appendChild(bepLabel);
    }
    if (current.marker && current.marker.comparable && show.head && current.series.head._yExtent) {
      var mx = mapRange(current.marker.flow, xExtent, left, width, false);
      var my = mapRange(current.marker.head, current.series.head._yExtent, top, height, true);
      plot.appendChild(svgEl("circle", { cx: mx, cy: my, r: 6, class: "curve-lab-point" }));
      var marker = svgEl("text", { x: mx + 8, y: my - 8, class: "curve-lab-label" });
      marker.textContent = phrase("curve_marker", "Physics Lab calculated point");
      plot.appendChild(marker);
    }
    plot._xExtent = xExtent;
    plot._left = left;
    plot._width = width;
    readProbe();
  }

  function nearest(points, flow) {
    var best = points[0];
    var bestGap = Infinity;
    points.forEach(function (point) {
      var gap = Math.abs(point.flow - flow);
      if (gap < bestGap) {
        best = point;
        bestGap = gap;
      }
    });
    return best;
  }

  function readProbe() {
    var readout = document.getElementById("curve-readout");
    if (!current || !plot._xExtent) {
      readout.textContent = "";
      return;
    }
    var probe = document.getElementById("curve-probe");
    var ratio = Number(probe.value) / 100;
    var flow = plot._xExtent.min + ratio * (plot._xExtent.max - plot._xExtent.min);
    var parts = ["Q " + flow.toFixed(2) + " " + current.display_units.flow];
    [
      ["show-head", "head", "curve_head", current.display_units.head],
      ["show-power", "shaft_power", "curve_power", current.display_units.power],
      ["show-eff", "efficiency", "curve_eff", current.display_units.efficiency],
    ].forEach(function (item) {
      if (!document.getElementById(item[0]).checked || !current.series[item[1]].length) {
        return;
      }
      var point = nearest(current.series[item[1]], flow);
      parts.push(phrase(item[2], item[1]) + " " + point.value.toFixed(2) + " " + item[3]);
    });
    readout.textContent = parts.join(" · ") + " · " + phrase("curve_nearest", "");
  }

  function paintCard() {
    var card = document.getElementById("curve-card");
    var basis = document.getElementById("curve-basis");
    var bep = document.getElementById("curve-bep");
    var warnings = document.getElementById("curve-warnings");
    if (!current) {
      card.textContent = phrase("curve_empty", "");
      return;
    }
    var source = current.source;
    card.textContent = [
      current.manufacturer,
      current.pump_model,
      current.frequency_hz + " Hz",
      current.speed_rpm + " rpm",
      phrase("curve_sg", "SG") + " " + current.specific_gravity_reference,
      phrase("curve_source", "Fuente") + " " + source.document + " p. " + source.page + (source.revision ? " " + source.revision : ""),
    ].join(" · ");
    if (current.basis.code === "total_estimate") {
      basis.textContent = phrase("curve_total", "N etapas").replace("{n}", String(current.basis.stages));
    } else {
      basis.textContent = phrase("curve_per_stage", "Por etapa");
    }
    if (current.bep && current.bep.origin === "sheet") {
      var units = current.display_units;
      bep.textContent = phrase("curve_bep_sheet", "BEP") + ": Q " + current.bep.flow.toFixed(1) + " " + units.flow
        + " · Head " + current.bep.head.toFixed(2) + " " + units.head
        + " · " + phrase("curve_power", "Shaft Power") + " " + current.bep.shaft_power.toFixed(3) + " " + units.power
        + " · " + phrase("curve_eff", "Efficiency") + " " + current.bep.efficiency_percent.toFixed(2) + " %";
    } else {
      bep.textContent = "";
    }
    warnings.replaceChildren();
    (current.warnings || []).forEach(function (warning) {
      var item = document.createElement("li");
      var known = {
        approximate_digitization: phrase("curve_approx", warning.message),
        per_stage_without_count: phrase("curve_no_compare", warning.message),
        outside_flow_range: phrase("curve_outside", warning.message),
        density_not_corrected: phrase("curve_density", warning.message),
      };
      item.textContent = known[warning.code] || warning.message;
      warnings.appendChild(item);
    });
    if (current.marker && current.marker.shaft_power_estimate) {
      var estimate = document.createElement("li");
      estimate.textContent = phrase("curve_estimate", "") + " "
        + current.marker.shaft_power_estimate.value.toFixed(3) + " " + current.marker.shaft_power_estimate.unit;
      warnings.appendChild(estimate);
    }
  }

  function loadCurve() {
    var id = document.getElementById("curve-speed").value;
    if (!id) {
      current = null;
      paintCard();
      draw();
      return;
    }
    getJson("/physics/api/curves/" + id + "/?" + query()).then(function (response) {
      if (!response.ok) {
        current = null;
        paintCard();
        draw();
        return;
      }
      current = response.data;
      return attachMarker();
    }).then(function () {
      paintCard();
      draw();
    }).catch(function () {
      document.getElementById("curve-card").textContent = phrase("curve_wait", "");
    });
  }

  function labResult() {
    if (window.EspPhysics && window.EspPhysics.lastResult) {
      return window.EspPhysics.lastResult;
    }
    try {
      return JSON.parse(sessionStorage.getItem("esp-lab-result") || "null");
    } catch (error) {
      return null;
    }
  }

  function attachMarker() {
    var lab = labResult();
    if (!lab || !current || !lab.results) {
      return null;
    }
    var stages = document.getElementById("curve-stages").value.trim();
    var body = {
      stages: stages ? Number(stages) : null,
      flow_unit: document.getElementById("curve-flow-unit").value,
      head_unit: document.getElementById("curve-head-unit").value,
      power_unit: document.getElementById("curve-power-unit").value,
      lab: {
        flow_m3_s: lab.results.flow_rate.si_value,
        head_m: lab.results.head.si_value,
        hydraulic_power_w: lab.results.hydraulic_power.si_value,
        density_kg_m3: lab.inputs.density.si_value,
      },
    };
    return postJson("/physics/api/curves/" + current.id + "/marker/", body).then(function (response) {
      if (response.ok) {
        current = response.data;
      }
    });
  }

  ["curve-manufacturer", "curve-series", "curve-model"].forEach(function (id) {
    document.getElementById(id).addEventListener("change", function () {
      refreshSelectors();
      loadCurve();
    });
  });
  ["curve-speed", "curve-stages", "curve-flow-unit", "curve-head-unit", "curve-power-unit"].forEach(function (id) {
    document.getElementById(id).addEventListener("change", loadCurve);
  });
  ["show-head", "show-power", "show-eff"].forEach(function (id) {
    document.getElementById(id).addEventListener("change", draw);
  });
  document.getElementById("curve-probe").addEventListener("input", readProbe);
  document.addEventListener("esp-lab-result", function () {
    if (!current) {
      return;
    }
    attachMarker().then(function () {
      paintCard();
      draw();
    });
  });

  getJson("/physics/api/curves/").then(function (response) {
    if (!response.ok || !response.data.curves) {
      document.getElementById("curve-card").textContent = phrase("curve_empty", "");
      return;
    }
    catalog = response.data.curves;
    refreshSelectors();
    loadCurve();
  }).catch(function () {
    document.getElementById("curve-card").textContent = phrase("curve_wait", "");
  });
})();
