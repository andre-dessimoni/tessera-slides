/* montin — keyboard.js
   ----------------------------------------------------------------------------
   Global key bindings for the deck. Inside the lightbox, arrows navigate
   thumbnails and Escape closes it; otherwise arrows change slide and the
   single-key shortcuts drive fullscreen/overview/sidebar/zoom.

   T.state: none.
   Calls: T.lbNavThumb, T.closeLightbox, T.navigate, T.toggleFullscreen,
          T.toggleOverview, T.toggleSidebar, T.deckZoom, T.deckZoomReset.
   Registers: T.onKey (boot wires the keydown listener).
   ------------------------------------------------------------------------- */
(function (T) {
  "use strict";

  function onKey(e) {
    if (e.target.tagName === "INPUT") return;
    var lb = document.getElementById("lightbox");
    var lbOpen = lb && !lb.classList.contains("hidden");
    if (lbOpen) {
      if (e.key === "ArrowRight" || e.key === "ArrowDown") { T.lbNavThumb(1); return; }
      if (e.key === "ArrowLeft"  || e.key === "ArrowUp")   { T.lbNavThumb(-1); return; }
      if (e.key === "Escape") { T.closeLightbox(); return; }
      return;
    }
    switch (e.key) {
      case "ArrowRight": case "ArrowDown":  T.navigate(1);  break;
      case "ArrowLeft":  case "ArrowUp":    T.navigate(-1); break;
      case "f": case "F": T.toggleFullscreen(); break;
      case "g": case "G": T.toggleOverview(); break;
      case "b": case "B": T.toggleSidebar(); break;
      case "+": case "=": T.deckZoom(1);  break;
      case "-": case "_": T.deckZoom(-1); break;
      case "0": T.deckZoomReset(); break;
    }
  }

  T.onKey = onKey;

})(window.Montin = window.Montin || {});
