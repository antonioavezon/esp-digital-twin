(function () {
  "use strict";

  var KEY = "esp-study-hz";
  var INITIAL = 60;
  var MIN = 30;
  var MAX = 90;

  function phrase(name, fallback) {
    var node = document.getElementById("drive-copy");
    if (!node) {
      return fallback;
    }
    try {
      var data = JSON.parse(node.textContent);
      return data[name] || fallback;
    } catch (error) {
      return fallback;
    }
  }

  function stored() {
    var raw = localStorage.getItem(KEY);
    var value = Number(raw);
    if (raw === null || !isFinite(value) || value < MIN || value > MAX) {
      return INITIAL;
    }
    return value;
  }

  function show(hz, error) {
    document.querySelectorAll("[data-drive-hz]").forEach(function (input) {
      if (document.activeElement === input && error) {
        return;
      }
      input.value = String(hz);
      input.setAttribute("aria-invalid", error ? "true" : "false");
    });
    document.querySelectorAll("[data-drive-error]").forEach(function (node) {
      node.hidden = !error;
      node.textContent = error || "";
    });
    document.querySelectorAll("[data-drive-status]").forEach(function (node) {
      node.textContent = phrase("vsd_current", "Valor guardado") + ": " + hz + " Hz. " + phrase("vsd_result", "");
    });
  }

  function commit(raw) {
    var text = String(raw).trim().replace(",", ".");
    if (!text) {
      show(stored(), phrase("vsd_empty", ""));
      return;
    }
    var value = Number(text);
    if (!isFinite(value) || value < MIN || value > MAX) {
      show(stored(), phrase("vsd_invalid", ""));
      return;
    }
    localStorage.setItem(KEY, String(value));
    show(value, "");
  }

  document.querySelectorAll("[data-drive-hz]").forEach(function (input) {
    input.addEventListener("change", function () {
      commit(input.value);
    });
  });
  document.querySelectorAll("[data-drive-reset]").forEach(function (button) {
    button.addEventListener("click", function () {
      localStorage.setItem(KEY, String(INITIAL));
      show(INITIAL, "");
    });
  });
  window.addEventListener("storage", function (event) {
    if (event.key === KEY) {
      show(stored(), "");
    }
  });
  show(stored(), "");
})();
