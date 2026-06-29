/* montin — stage.js
   ----------------------------------------------------------------------------
   Fixed-size ("PDF-like") decks: scale the native-size .stage to fit #main and
   add grab-to-pan when it overflows. No-op for fluid decks.

   T.state: reads deckZoom, slides, current.
   Calls: T.renderTabulatorsInSlide (redraw after re-fit).
   Registers: T.fitStage, T.initStage.
   ------------------------------------------------------------------------- */
(function (T) {
  "use strict";

  // -- Fixed-size stage (scale-to-fit) --------------------
  function fitStage() {
    var body = document.body;
    if (!body.classList.contains("fixed-size")) return;
    var main = document.getElementById("main");
    if (!main) return;

    var W = parseFloat(body.dataset.width) || 1366;
    var H = parseFloat(body.dataset.height) || 768;
    var scaleUp = body.dataset.scaleUp === "true";
    var keepAspect = body.dataset.keepAspect !== "false";

    var sx = main.clientWidth / W;
    var sy = main.clientHeight / H;
    if (!scaleUp) { sx = Math.min(1, sx); sy = Math.min(1, sy); }
    if (keepAspect) { sx = sy = Math.min(sx, sy); }

    // Deck-area zoom multiplies the fit (fixed-size stages scale via transform).
    sx *= T.state.deckZoom; sy *= T.state.deckZoom;

    body.style.setProperty("--stage-sx", sx);
    body.style.setProperty("--stage-sy", sy);

    // When the scaled stage is larger than the viewport, #main scrolls — flag it
    // so the cursor shows it is grab-pannable.
    var over = (W * sx > main.clientWidth + 1) || (H * sy > main.clientHeight + 1);
    main.classList.toggle("can-pan", over);
  }

  // Drag-to-pan the zoomed stage. Native scrollbars/wheel also work; this adds
  // grab-panning from empty (non-interactive) areas without hijacking clicks on
  // cells, links, inputs, or Plotly charts.
  function initStagePan() {
    var main = document.getElementById("main");
    if (!main) return;
    var dragging = false, startX, startY, startL, startT;
    main.addEventListener("mousedown", function (e) {
      if (e.button !== 0 || !main.classList.contains("can-pan")) return;
      if (e.target.closest(".cell, a, button, input, textarea, select, .plotly-container")) return;
      dragging = true;
      startX = e.clientX; startY = e.clientY;
      startL = main.scrollLeft; startT = main.scrollTop;
      main.classList.add("panning");
      e.preventDefault();
    });
    document.addEventListener("mousemove", function (e) {
      if (!dragging) return;
      main.scrollLeft = startL - (e.clientX - startX);
      main.scrollTop  = startT - (e.clientY - startY);
    });
    document.addEventListener("mouseup", function () {
      if (dragging) { dragging = false; main.classList.remove("panning"); }
    });
  }

  function initStage() {
    if (!document.body.classList.contains("fixed-size")) return;
    fitStage();
    var main = document.getElementById("main");
    // Recompute the stage scale, then redraw the visible tables so Tabulator
    // re-measures against the new transform.
    var onFit = function() {
      fitStage();
      T.renderTabulatorsInSlide(T.state.slides[T.state.current]);
    };
    // ResizeObserver on #main captures window resizes (it is pinned to the
    // window edges) and sidebar toggle/resize (which shifts its left edge).
    if (main && "ResizeObserver" in window) {
      new ResizeObserver(onFit).observe(main);
    } else {
      window.addEventListener("resize", onFit);
    }
    initStagePan();
  }

  T.fitStage  = fitStage;
  T.initStage = initStage;

})(window.Montin = window.Montin || {});
