(function () {
  "use strict";

  window.EspPhysics = window.EspPhysics || {};

  function polyline(svg, points) {
    var node = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
    node.setAttribute("points", points.join(" "));
    svg.appendChild(node);
  }

  window.EspPhysics.drawChart = function (svgId, noteId, series) {
    var svg = document.getElementById(svgId);
    var note = document.getElementById(noteId);
    if (!svg || !series) {
      return;
    }
    svg.replaceChildren();
    if (note) {
      note.textContent = series.note;
    }
    var title = document.getElementById(svgId + "-title");
    if (title && series.title) {
      title.textContent = series.title;
    }
    var coords = series.points.map(function (point) {
      var x = 28 + (point.plot_x / 100) * 270;
      var y = 156 - (point.plot_y / 100) * 130;
      return x.toFixed(2) + "," + y.toFixed(2);
    });
    polyline(svg, coords);
  };
})();
