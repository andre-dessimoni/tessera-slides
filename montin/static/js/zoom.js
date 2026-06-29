/* montin — zoom.js
   ----------------------------------------------------------------------------
   Deck-area zoom (toolbar +/- buttons, +/-/0 keys, and pinch). Scales only the
   slide content via the --deck-zoom CSS var (fluid decks) or the stage transform
   (fixed-size decks).

   T.state: reads/writes deckZoom; reads slides, current.
   Calls: T.fitStage, T.renderTabulatorsInSlide.
   Registers: T.applyDeckZoom, T.deckZoom, T.deckZoomReset, T.setDeckZoomLive.
   ------------------------------------------------------------------------- */
(function (T) {
  "use strict";

  // Module-local zoom bounds/step (only zoom.js needs them).
  var ZOOM_MIN = 0.25, ZOOM_MAX = 4, ZOOM_STEP = 1.25;

  // Full zoom apply: update the CSS var + label, re-fit a fixed-size stage, and
  // re-render the visible tables (the expensive part — see setDeckZoomLive).
  function applyDeckZoom() {
    document.body.style.setProperty("--deck-zoom", T.state.deckZoom);
    var lvl = document.getElementById("zoom-level");
    if (lvl) lvl.textContent = Math.round(T.state.deckZoom * 100) + "%";
    // Fixed-size stages scale through the transform fit; recompute it.
    if (document.body.classList.contains("fixed-size")) T.fitStage();
    T.renderTabulatorsInSlide(T.state.slides[T.state.current]);
  }

  function deckZoom(dir) {
    var z = dir > 0 ? T.state.deckZoom * ZOOM_STEP : T.state.deckZoom / ZOOM_STEP;
    T.state.deckZoom = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, Math.round(z * 100) / 100));
    applyDeckZoom();
  }

  function deckZoomReset() {
    T.state.deckZoom = 1;
    applyDeckZoom();
  }

  // Lightweight zoom update for live pinch frames. Mirrors applyDeckZoom but
  // skips the expensive Tabulator re-render (run once when the pinch ends).
  function setDeckZoomLive(z) {
    T.state.deckZoom = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, z));
    document.body.style.setProperty("--deck-zoom", T.state.deckZoom);
    var lvl = document.getElementById("zoom-level");
    if (lvl) lvl.textContent = Math.round(T.state.deckZoom * 100) + "%";
    if (document.body.classList.contains("fixed-size")) T.fitStage();
  }

  T.applyDeckZoom   = applyDeckZoom;
  T.deckZoom        = deckZoom;
  T.deckZoomReset   = deckZoomReset;
  T.setDeckZoomLive = setDeckZoomLive;

})(window.Montin = window.Montin || {});
