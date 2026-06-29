/* montin — view.js
   ----------------------------------------------------------------------------
   Small chrome toggles: fullscreen, the overview grid, and the cell-expand
   modal.

   T.state: none.   Calls: none.
   Registers: T.toggleFullscreen, T.toggleOverview, T.expandCell, T.closeModal.
   ------------------------------------------------------------------------- */
(function (T) {
  "use strict";

  // -- Fullscreen ------------------------------------------
  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(function() {});
    } else {
      document.exitFullscreen().catch(function() {});
    }
  }

  // -- Overview --------------------------------------------
  function toggleOverview() {
    var ov = document.getElementById("overview");
    if (ov) ov.classList.toggle("hidden");
  }

  // -- Modal (expand) -------------------------------------
  function expandCell(btn) {
    var cell = btn.closest(".cell");
    var body = cell && cell.querySelector(".cell-body");
    if (!body) return;
    var modal = document.getElementById("modal");
    var modalBody = document.getElementById("modal-body");
    if (!modal || !modalBody) return;
    modalBody.innerHTML = body.innerHTML;
    modal.classList.remove("hidden");
  }

  function closeModal() {
    var modal = document.getElementById("modal");
    if (modal) modal.classList.add("hidden");
  }

  T.toggleFullscreen = toggleFullscreen;
  T.toggleOverview   = toggleOverview;
  T.expandCell       = expandCell;
  T.closeModal       = closeModal;

})(window.Montin = window.Montin || {});
