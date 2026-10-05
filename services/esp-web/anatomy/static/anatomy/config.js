(function () {
  "use strict";
  var form = document.getElementById("config-form");
  if (!form) {
    return;
  }
  form.querySelectorAll("input").forEach(function (input) {
    input.addEventListener("change", function () {
      form.submit();
    });
  });
})();
