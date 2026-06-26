/* tessera — boot.js
   ----------------------------------------------------------------------------
   Loads LAST. Wires the global event listeners, runs each module's initialiser
   in order, re-exports the HTML-facing API (called from inline onclick=...) onto
   window, and boots once the DOM is ready.

   T.state: reads slides, current (deep-link to the hash slide).
   Calls: every module's init and event handlers.   Registers: nothing new on T.
   ------------------------------------------------------------------------- */
(function (T) {
  "use strict";

  function init() {
    if (T.state.slides.length === 0) return;

    // Deep link via hash (#slide-3)
    var hash = window.location.hash.slice(1);
    var fromHash = T.state.slides.findIndex(function (s) { return s.id === hash; });
    T.goTo(fromHash >= 0 ? fromHash : 0, false);

    window.addEventListener("keydown", T.onKey);
    window.addEventListener("hashchange", T.onHashChange);

    T.initPlotlyCharts();
    T.initSliders();
    T.initLightbox();
    T.initSidebar();
    T.initSidebarSections();
    T.initToolbar();
    T.initStage();
    T.initTouchGestures();
    T.initChartPrinting();
    T.applyDeckZoom();
  }

  // -- Expose global functions ----------------------------
  // Templates call these bare (e.g. onclick="navigate(1)"), so mirror the deck
  // API from the namespace onto window. Add new HTML-facing functions here.
  window.toggleSidebar          = T.toggleSidebar;
  window.navigate               = T.navigate;
  window.goToSlide              = T.goToSlide;
  window.goToIndex              = T.goToIndex;
  window.toggleFullscreen       = T.toggleFullscreen;
  window.toggleOverview         = T.toggleOverview;
  window.expandCell             = T.expandCell;
  window.expandPlotly           = T.expandPlotly;
  window.closeModal             = T.closeModal;
  window.openLightbox           = T.openLightbox;
  window.openLightboxFromSlider = T.openLightboxFromSlider;
  window.closeLightbox          = T.closeLightbox;
  window.lbGoTo                 = T.lbGoTo;
  window.lbNavThumb             = T.lbNavThumb;
  window.lbResetZoom            = T.lbResetZoom;
  window.copyCell               = T.copyCell;
  window.copyImage              = T.copyImage;
  window.sliderNav              = T.sliderNav;
  window.filterSidebar          = T.filterSidebar;
  window.toggleSection          = T.toggleSection;
  window.toggleRegexMode        = T.toggleRegexMode;
  window.collapseAllSections    = T.collapseAllSections;
  window.expandAllSections      = T.expandAllSections;
  window.collapseLevel          = T.collapseLevel;
  window.expandLevel            = T.expandLevel;
  window.deckZoom               = T.deckZoom;
  window.deckZoomReset          = T.deckZoomReset;

  // -- Boot -----------------------------------------------
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

})(window.Tessera = window.Tessera || {});
