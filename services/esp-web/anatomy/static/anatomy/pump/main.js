(function () {
  "use strict";

  var root = document.getElementById("pump-app");
  if (!root || !window.EspPump) {
    return;
  }
  window.EspPump.controls(root);

  var payloadNode = document.getElementById("pump-payload");
  if (!payloadNode || !payloadNode.textContent.trim()) {
    return;
  }
  var payload = null;
  try {
    payload = JSON.parse(payloadNode.textContent);
  } catch (error) {
    payload = null;
  }
  if (!payload || !payload.stages || !payload.flow_path) {
    return;
  }
  window.EspPump.navigation(root, payload);
})();
