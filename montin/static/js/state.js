/* montin — state.js
   ----------------------------------------------------------------------------
   Creates the shared `Montin` namespace (aliased `T`) and the single source of
   truth for cross-module mutable state, `T.state`. MUST load first: every other
   module assumes `window.Montin` and `T.state` already exist.

   See README.md in this folder for the module architecture and the rules for
   what belongs on `T` / `T.state` / `window`.

   Registers: T.state (shared state object).
   ------------------------------------------------------------------------- */
(function (T) {
  "use strict";

  // Cross-module mutable state. Only values read or written by more than one
  // module live here; per-feature state stays local to its own module.
  T.state = {
    slides:       Array.from(document.querySelectorAll(".slide")), // never reassigned
    current:      0,      // index of the active slide (navigation, zoom, lightbox)
    deckZoom:     1,      // deck-area zoom factor, 1 = 100% (zoom, stage, touch)
    searchActive: false,  // sidebar filter active? (navigation, sidebar)
  };

})(window.Montin = window.Montin || {});
