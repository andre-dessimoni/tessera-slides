/* montin — slider.js
   ----------------------------------------------------------------------------
   Per-slide image sliders: show one slide at a time, sync the dots, and wire the
   prev/next + dot controls.

   T.state: none.   Calls: none.
   Registers: T.initSliders, T.sliderNav.
   ------------------------------------------------------------------------- */
(function (T) {
  "use strict";

  // Per-slider state: id -> { current }
  var _sliders = {};

  function initSliders() {
    document.querySelectorAll(".cell-image-slider").forEach(function(cell) {
      var track = cell.querySelector(".slider-track");
      if (!track) return;
      var id = track.id;
      _sliders[id] = { current: 0 };
      _sliderUpdate(id, cell);
    });
  }

  function sliderNav(btn, delta) {
    var cell = btn.closest(".cell-image-slider");
    var track = cell && cell.querySelector(".slider-track");
    if (!track) return;
    var id = track.id;
    var total = track.querySelectorAll(".slider-slide").length;
    var st = _sliders[id] || { current: 0 };
    st.current = (st.current + delta + total) % total;
    _sliders[id] = st;
    _sliderUpdate(id, cell);
  }

  function _sliderUpdate(id, cell) {
    var track = document.getElementById(id);
    if (!track) return;
    var st = _sliders[id] || { current: 0 };
    var slideEls = track.querySelectorAll(".slider-slide");
    slideEls.forEach(function(el, i) {
      el.style.display = i === st.current ? "" : "none";
    });
    // Update dots
    var dots = cell.querySelectorAll(".slider-dot");
    dots.forEach(function(d, i) {
      d.classList.toggle("active", i === st.current);
    });
    // Update dot click handlers
    dots.forEach(function(d) {
      d.onclick = function() {
        var idx = parseInt(d.getAttribute("data-index"), 10);
        _sliders[id].current = idx;
        _sliderUpdate(id, cell);
      };
    });
  }

  T.initSliders = initSliders;
  T.sliderNav   = sliderNav;

})(window.Montin = window.Montin || {});
