/* montin — lightbox.js
   ----------------------------------------------------------------------------
   Full-screen image viewer with mouse-wheel/pinch-less zoom, drag/touch pan,
   and a thumbnail strip built from every image in the active slide.

   Also owns the shared image-src helpers (_svgDataUri / _imgSrc) used by copy.js.

   T.state: reads slides, current.   Calls: none.
   Registers: T.initLightbox, T.openLightbox, T.openLightboxFromSlider,
              T.closeLightbox, T.lbGoTo, T.lbNavThumb, T.lbResetZoom, T._imgSrc.
   ------------------------------------------------------------------------- */
(function (T) {
  "use strict";

  // Internal lightbox state (local — only this module touches it).
  var _lb = {
    images: [],      // [{src, alt}]
    index: 0,
    zoom: 1,
    panX: 0,
    panY: 0,
    dragging: false,
    startX: 0,
    startY: 0,
    lastPanX: 0,
    lastPanY: 0,
  };

  function initLightbox() {
    var lb = document.getElementById("lightbox");
    if (!lb) return;

    var lbImg = document.getElementById("lightbox-img");

    // Zoom via mouse wheel
    lb.addEventListener("wheel", function(e) {
      if (lb.classList.contains("hidden")) return;
      e.preventDefault();
      var delta = e.deltaY > 0 ? -0.15 : 0.15;
      _lb.zoom = Math.max(0.3, Math.min(8, _lb.zoom + delta));
      applyLbTransform();
    }, { passive: false });

    // Pan via drag
    lbImg && lbImg.addEventListener("mousedown", function(e) {
      if (e.button !== 0) return;
      _lb.dragging = true;
      _lb.startX = e.clientX - _lb.panX;
      _lb.startY = e.clientY - _lb.panY;
      lbImg.style.cursor = "grabbing";
      e.preventDefault();
    });
    document.addEventListener("mousemove", function(e) {
      if (!_lb.dragging) return;
      _lb.panX = e.clientX - _lb.startX;
      _lb.panY = e.clientY - _lb.startY;
      applyLbTransform();
    });
    document.addEventListener("mouseup", function() {
      if (_lb.dragging) {
        _lb.dragging = false;
        var lbImg2 = document.getElementById("lightbox-img");
        if (lbImg2) lbImg2.style.cursor = "grab";
      }
    });

    // Touch pan
    lbImg && lbImg.addEventListener("touchstart", function(e) {
      if (e.touches.length === 1) {
        _lb.dragging = true;
        _lb.startX = e.touches[0].clientX - _lb.panX;
        _lb.startY = e.touches[0].clientY - _lb.panY;
      }
    }, { passive: true });
    lbImg && lbImg.addEventListener("touchmove", function(e) {
      if (!_lb.dragging || e.touches.length !== 1) return;
      _lb.panX = e.touches[0].clientX - _lb.startX;
      _lb.panY = e.touches[0].clientY - _lb.startY;
      applyLbTransform();
    }, { passive: true });
    lbImg && lbImg.addEventListener("touchend", function() {
      _lb.dragging = false;
    });
  }

  function applyLbTransform() {
    var lbImg = document.getElementById("lightbox-img");
    if (!lbImg) return;
    lbImg.style.transform = "translate(" + _lb.panX + "px, " + _lb.panY + "px) scale(" + _lb.zoom + ")";
  }

  function _resetLbView() {
    _lb.zoom = 1; _lb.panX = 0; _lb.panY = 0;
    applyLbTransform();
  }

  /**
   * Serialize an inline <svg> (e.g. a matplotlib SVG figure) to a data URI so it
   * can be shown in the lightbox or copied like any other image.
   */
  function _svgDataUri(el) {
    var svg = el.tagName && el.tagName.toLowerCase() === "svg" ? el : el.querySelector("svg");
    if (!svg) return "";
    var s = new XMLSerializer().serializeToString(svg);
    return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(s);
  }

  /** Resolve the displayable image src of a trigger element (<img> or inline SVG). */
  function _imgSrc(el) {
    if (!el) return "";
    if (el.tagName === "IMG") return el.src;
    return _svgDataUri(el);
  }

  /**
   * Collects all images from the current slide (cell-image + sliders).
   * Returns [{src, alt}].
   */
  function _collectSlideImages() {
    var currentSlide = T.state.slides[T.state.current];
    if (!currentSlide) return [];
    var imgs = [];
    // Regular images and inline-SVG figures (cell-image)
    currentSlide.querySelectorAll(".cell-image .lightbox-trigger").forEach(function(el) {
      var src = _imgSrc(el);
      if (src) imgs.push({ src: src, alt: el.getAttribute("alt") || "" });
    });
    // Sliders: collect all images from each slider
    currentSlide.querySelectorAll(".cell-image-slider .slider-img").forEach(function(img) {
      imgs.push({ src: img.src, alt: img.alt || "" });
    });
    return imgs;
  }

  function openLightbox(imgEl) {
    _lb.images = _collectSlideImages();
    var src = _imgSrc(imgEl);
    _lb.index = _lb.images.findIndex(function(im) { return im.src === src; });
    if (_lb.index < 0) { _lb.index = 0; }
    _lbShow();
  }

  function openLightboxFromSlider(imgEl) {
    openLightbox(imgEl);
  }

  function _lbShow() {
    var lb = document.getElementById("lightbox");
    var lbImg = document.getElementById("lightbox-img");
    if (!lb || !lbImg || _lb.images.length === 0) return;

    var im = _lb.images[_lb.index];
    // Keep zoom/pan when switching images (no reset here)
    lbImg.src = im.src;
    lbImg.alt = im.alt;
    lbImg.style.cursor = "grab";
    lb.classList.remove("hidden");

    _lbRenderThumbs();
  }

  function _lbRenderThumbs() {
    var container = document.getElementById("lightbox-thumbs");
    if (!container) return;
    container.innerHTML = "";
    _lb.images.forEach(function(im, i) {
      var thumb = document.createElement("img");
      thumb.src = im.src;
      thumb.alt = im.alt;
      thumb.className = "lb-thumb" + (i === _lb.index ? " lb-thumb-active" : "");
      thumb.onclick = (function(idx) { return function() { lbGoTo(idx); }; })(i);
      container.appendChild(thumb);
    });
    // Scroll active thumbnail into view
    var active = container.querySelector(".lb-thumb-active");
    if (active) active.scrollIntoView({ block: "nearest", inline: "center" });
  }

  function lbGoTo(idx) {
    if (idx < 0 || idx >= _lb.images.length) return;
    _lb.index = idx;
    // Keep zoom and pan when navigating between images
    _lbShow();
  }

  function lbNavThumb(delta) {
    lbGoTo(_lb.index + delta);
  }

  function lbResetZoom() {
    _resetLbView();
  }

  function closeLightbox() {
    var lb = document.getElementById("lightbox");
    if (lb) lb.classList.add("hidden");
    _resetLbView();
  }

  T.initLightbox          = initLightbox;
  T.openLightbox          = openLightbox;
  T.openLightboxFromSlider = openLightboxFromSlider;
  T.closeLightbox         = closeLightbox;
  T.lbGoTo                = lbGoTo;
  T.lbNavThumb            = lbNavThumb;
  T.lbResetZoom           = lbResetZoom;
  T._imgSrc               = _imgSrc;   // shared with copy.js

})(window.Montin = window.Montin || {});
