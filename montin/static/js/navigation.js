/* montin — navigation.js
   ----------------------------------------------------------------------------
   Moving between slides: activate a slide + its sidebar item, sync the counter
   and URL hash, and trigger lazy chart/table rendering for the slide shown.

   T.state: reads/writes current; reads slides, searchActive.
   Calls: T.resizePlotlyInSlide, T.renderMermaidInSlide,
          T.renderTabulatorsInSlide, T.revealActiveSidebarItem.
   Registers: T.goTo, T.navigate, T.goToSlide, T.goToIndex, T.onHashChange.
   ------------------------------------------------------------------------- */
(function (T) {
  "use strict";

  function goTo(index, pushHash) {
    var slides = T.state.slides;
    if (pushHash === undefined) pushHash = true;
    if (index < 0 || index >= slides.length) return;

    slides[T.state.current].classList.remove("active");
    var sidebarItems = document.querySelectorAll(".sidebar-item");
    if (sidebarItems[T.state.current]) sidebarItems[T.state.current].classList.remove("active");

    T.state.current = index;
    slides[T.state.current].classList.add("active");
    if (sidebarItems[T.state.current]) sidebarItems[T.state.current].classList.add("active");

    var input = document.getElementById("slide-input");
    if (input) input.value = T.state.current + 1;

    var sidebarItem = sidebarItems[T.state.current];
    if (sidebarItem) sidebarItem.scrollIntoView({ block: "nearest" });

    if (pushHash) {
      history.replaceState(null, "", "#" + slides[T.state.current].id);
    }

    T.resizePlotlyInSlide(slides[T.state.current]);
    T.renderMermaidInSlide(slides[T.state.current]);
    T.renderTabulatorsInSlide(slides[T.state.current]);
    T.revealActiveSidebarItem();
  }

  // Step in the direction of delta. While a search filter is active, skip
  // non-matching (hidden) items. Otherwise step to the immediate neighbour even
  // if it sits inside a collapsed section — goTo() -> revealActiveSidebarItem()
  // expands its ancestors so arrow keys can move into and unfold a folded node.
  function navigate(delta) {
    var slides = T.state.slides;
    var step = delta < 0 ? -1 : 1;
    if (!T.state.searchActive) {
      goTo(T.state.current + step);
      return;
    }
    var items = document.querySelectorAll(".sidebar-item");
    var i = T.state.current + step;
    while (i >= 0 && i < slides.length) {
      var it = items[i];
      if (!it || !it.classList.contains("sidebar-hidden")) { goTo(i); return; }
      i += step;
    }
    // no visible slide in that direction -> stay put
  }

  function goToSlide(slideId) {
    var idx = T.state.slides.findIndex(function(s) { return s.id === slideId; });
    if (idx >= 0) goTo(idx);
  }

  function goToIndex(n) {
    goTo(Math.max(1, Math.min(n, T.state.slides.length)) - 1);
  }

  function onHashChange() {
    var id = window.location.hash.slice(1);
    var idx = T.state.slides.findIndex(function(s) { return s.id === id; });
    if (idx >= 0) goTo(idx, false);
  }

  T.goTo         = goTo;
  T.navigate     = navigate;
  T.goToSlide    = goToSlide;
  T.goToIndex    = goToIndex;
  T.onHashChange = onHashChange;

})(window.Montin = window.Montin || {});
