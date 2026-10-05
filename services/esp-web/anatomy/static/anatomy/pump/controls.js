(function () {
  "use strict";

  window.EspPump = window.EspPump || {};

  window.EspPump.controls = function (root) {
    var play = root.querySelector("#pump-play");
    var pause = root.querySelector("#pump-pause");
    var fluid = root.querySelector("#pump-fluid");
    if (!play || !pause || !fluid) {
      return;
    }

    function setSpin(on) {
      root.classList.toggle("is-spinning", on);
      play.setAttribute("aria-pressed", on ? "true" : "false");
      pause.setAttribute("aria-pressed", on ? "false" : "true");
    }

    play.addEventListener("click", function () {
      setSpin(true);
    });
    pause.addEventListener("click", function () {
      setSpin(false);
    });
    fluid.addEventListener("click", function () {
      var on = root.classList.toggle("show-fluid");
      fluid.setAttribute("aria-pressed", on ? "true" : "false");
    });
    setSpin(false);
  };
})();
