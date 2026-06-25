/* tessera — main.js
   Navigation, fullscreen, overview, modal, lightbox (zoom/pan/thumbnails),
   image slider, plotly / tabulator init.
   No external dependencies (Plotly / Tabulator are initialised if present).
*/

(function () {
  "use strict";

  // -- State -----------------------------------------------
  const slides = Array.from(document.querySelectorAll(".slide"));
  let current = 0;
  var _savedSidebarWidth = "220px";

  // Deck-area zoom (toolbar +/- controls). Scales only the slide content, not
  // the sidebar/toolbar. 1 = 100%.
  var _deckZoom = 1;
  var ZOOM_MIN = 0.25, ZOOM_MAX = 4, ZOOM_STEP = 1.25;

  // Touch gestures on the deck (see initTouchGestures): one-finger swipe to
  // change slide, two-finger pinch to drive the deck zoom.
  var _touch = { startX: 0, startY: 0, swiping: false,
                 pinching: false, startDist: 0, startZoom: 1, lockedAfterPinch: false };
  var SWIPE_MIN = 50; // px of horizontal travel to count as a swipe

  // -- Initialisation -------------------------------------
  function init() {
    if (slides.length === 0) return;

    // Deep link via hash (#slide-3)
    const hash = window.location.hash.slice(1);
    const fromHash = slides.findIndex((s) => s.id === hash);
    goTo(fromHash >= 0 ? fromHash : 0, false);

    window.addEventListener("keydown", onKey);
    window.addEventListener("hashchange", onHashChange);

    initPlotlyCharts();
    initSliders();
    initLightbox();
    initSidebar();
    initSidebarSections();
    initToolbar();
    initStage();
    initTouchGestures();
    applyDeckZoom();
  }

  // -- Responsive toolbar ---------------------------------
  // The toolbar wraps onto extra rows on narrow viewports (see layout.css).
  // Mirror its real height into --toolbar-height so #main / #sidebar reserve
  // the right amount of space instead of being overlapped by the wrapped rows.
  function initToolbar() {
    var toolbar = document.getElementById("toolbar");
    if (!toolbar) return;
    var sync = function () {
      document.documentElement.style.setProperty(
        "--toolbar-height", toolbar.offsetHeight + "px");
    };
    sync();
    // The toolbar's height only changes when its content reflows (wrap), which a
    // ResizeObserver on the element captures directly; window resize is covered
    // because it changes the toolbar's available width.
    if ("ResizeObserver" in window) {
      new ResizeObserver(sync).observe(toolbar);
    } else {
      window.addEventListener("resize", sync);
    }
  }

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
    sx *= _deckZoom; sy *= _deckZoom;

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
    var onFit = function() { fitStage(); renderTabulatorsInSlide(slides[current]); };
    // ResizeObserver on #main captures window resizes (it is pinned to the
    // window edges) and sidebar toggle/resize (which shifts its left edge).
    if (main && "ResizeObserver" in window) {
      new ResizeObserver(onFit).observe(main);
    } else {
      window.addEventListener("resize", onFit);
    }
    initStagePan();
  }

  // -- Deck-area zoom (toolbar) ---------------------------
  function applyDeckZoom() {
    document.body.style.setProperty("--deck-zoom", _deckZoom);
    var lvl = document.getElementById("zoom-level");
    if (lvl) lvl.textContent = Math.round(_deckZoom * 100) + "%";
    // Fixed-size stages scale through the transform fit; recompute it.
    if (document.body.classList.contains("fixed-size")) fitStage();
    renderTabulatorsInSlide(slides[current]);
  }

  function deckZoom(dir) {
    var z = dir > 0 ? _deckZoom * ZOOM_STEP : _deckZoom / ZOOM_STEP;
    _deckZoom = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, Math.round(z * 100) / 100));
    applyDeckZoom();
  }

  function deckZoomReset() {
    _deckZoom = 1;
    applyDeckZoom();
  }

  // Lightweight zoom update for live pinch frames. Mirrors applyDeckZoom but
  // skips the expensive Tabulator re-render (run once when the pinch ends).
  function setDeckZoomLive(z) {
    _deckZoom = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, z));
    document.body.style.setProperty("--deck-zoom", _deckZoom);
    var lvl = document.getElementById("zoom-level");
    if (lvl) lvl.textContent = Math.round(_deckZoom * 100) + "%";
    if (document.body.classList.contains("fixed-size")) fitStage();
  }

  // -- Touch gestures (swipe to navigate, pinch to zoom) --
  // One finger: a mostly-horizontal swipe past SWIPE_MIN switches slides (left ->
  // next, right -> previous), but only while the slide fits (deck zoom <= 100% and
  // no horizontal overflow) so a zoomed-in slide can still be panned natively.
  // Two fingers: pinch drives the existing deck zoom. #main has touch-action:
  // pan-x pan-y (layout.css) so the browser's own pinch/double-tap zoom is off and
  // we can preventDefault here.
  function initTouchGestures() {
    var main = document.getElementById("main");
    if (!main) return;

    function dist(t) {
      var dx = t[0].clientX - t[1].clientX;
      var dy = t[0].clientY - t[1].clientY;
      return Math.hypot(dx, dy);
    }

    // A horizontal swipe starting here should be left to the element (a control
    // that wants the drag, or something the user scrolls sideways) rather than
    // switching slides. Walk up to #main looking for an interactive target or an
    // ancestor that scrolls horizontally (wide tables, code blocks, etc.).
    function swipeBlocked(target) {
      if (target.closest("a, button, input, textarea, select, .plotly-container, .cell-image-slider")) return true;
      for (var el = target; el && el !== main; el = el.parentElement) {
        if (el.nodeType !== 1) continue;
        if (el.scrollWidth > el.clientWidth + 1) {
          var ox = getComputedStyle(el).overflowX;
          if (ox === "auto" || ox === "scroll") return true;
        }
      }
      return false;
    }

    function startPinch(e) {
      _touch.pinching = true;
      _touch.swiping = false;
      _touch.startDist = dist(e.touches);
      _touch.startZoom = _deckZoom;
    }

    main.addEventListener("touchstart", function (e) {
      var lb = document.getElementById("lightbox");
      if (lb && !lb.classList.contains("hidden")) return; // lightbox has its own

      if (e.touches.length === 2) {
        startPinch(e);
        e.preventDefault();
        return;
      }

      if (e.touches.length === 1 && !_touch.pinching && !_touch.lockedAfterPinch) {
        // Only swipe-navigate when the slide fits; otherwise let it pan.
        if (_deckZoom > 1 || main.scrollWidth > main.clientWidth + 1) return;
        if (swipeBlocked(e.target)) return;
        _touch.swiping = true;
        _touch.startX = e.touches[0].clientX;
        _touch.startY = e.touches[0].clientY;
      }
    }, { passive: false });

    main.addEventListener("touchmove", function (e) {
      // A second finger can arrive without a fresh 2-touch touchstart reaching us
      // (e.g. DevTools emulation); pick up the pinch here too.
      if (e.touches.length === 2) {
        if (!_touch.pinching) { startPinch(e); e.preventDefault(); return; }
        var ratio = dist(e.touches) / (_touch.startDist || 1);
        setDeckZoomLive(_touch.startZoom * ratio);
        e.preventDefault();
      }
    }, { passive: false });

    function onEnd(e) {
      if (_touch.swiping) {
        var t = e.changedTouches[0];
        var dx = t.clientX - _touch.startX;
        var dy = t.clientY - _touch.startY;
        if (Math.abs(dx) >= SWIPE_MIN && Math.abs(dx) > Math.abs(dy) * 1.5) {
          navigate(dx < 0 ? 1 : -1); // swipe left -> next, swipe right -> previous
        }
        _touch.swiping = false;
      }
      if (_touch.pinching && e.touches.length < 2) {
        _touch.pinching = false;
        _touch.lockedAfterPinch = true; // ignore the leftover finger as a swipe
        applyDeckZoom(); // finalize with the full (table re-render) path
      }
      if (e.touches.length === 0) {
        _touch.lockedAfterPinch = false;
      }
    }
    main.addEventListener("touchend", onEnd, { passive: true });
    main.addEventListener("touchcancel", onEnd, { passive: true });
  }

  // -- Navigation -----------------------------------------
  function goTo(index, pushHash) {
    if (pushHash === undefined) pushHash = true;
    if (index < 0 || index >= slides.length) return;

    slides[current].classList.remove("active");
    var sidebarItems = document.querySelectorAll(".sidebar-item");
    if (sidebarItems[current]) sidebarItems[current].classList.remove("active");

    current = index;
    slides[current].classList.add("active");
    if (sidebarItems[current]) sidebarItems[current].classList.add("active");

    var input = document.getElementById("slide-input");
    if (input) input.value = current + 1;

    var sidebarItem = sidebarItems[current];
    if (sidebarItem) sidebarItem.scrollIntoView({ block: "nearest" });

    if (pushHash) {
      history.replaceState(null, "", "#" + slides[current].id);
    }

    resizePlotlyInSlide(slides[current]);
    renderMermaidInSlide(slides[current]);
    renderTabulatorsInSlide(slides[current]);
    revealActiveSidebarItem();
  }

  // Step in the direction of delta. While a search filter is active, skip
  // non-matching (hidden) items. Otherwise step to the immediate neighbour even
  // if it sits inside a collapsed section — goTo() -> revealActiveSidebarItem()
  // expands its ancestors so arrow keys can move into and unfold a folded node.
  function navigate(delta) {
    var step = delta < 0 ? -1 : 1;
    if (!_searchActive) {
      goTo(current + step);
      return;
    }
    var items = document.querySelectorAll(".sidebar-item");
    var i = current + step;
    while (i >= 0 && i < slides.length) {
      var it = items[i];
      if (!it || !it.classList.contains("sidebar-hidden")) { goTo(i); return; }
      i += step;
    }
    // no visible slide in that direction -> stay put
  }

  function goToSlide(slideId) {
    var idx = slides.findIndex(function(s) { return s.id === slideId; });
    if (idx >= 0) goTo(idx);
  }

  function goToIndex(n) {
    goTo(Math.max(1, Math.min(n, slides.length)) - 1);
  }

  function onHashChange() {
    var id = window.location.hash.slice(1);
    var idx = slides.findIndex(function(s) { return s.id === id; });
    if (idx >= 0) goTo(idx, false);
  }

  // -- Keyboard --------------------------------------------
  function onKey(e) {
    if (e.target.tagName === "INPUT") return;
    var lb = document.getElementById("lightbox");
    var lbOpen = lb && !lb.classList.contains("hidden");
    if (lbOpen) {
      if (e.key === "ArrowRight" || e.key === "ArrowDown") { lbNavThumb(1); return; }
      if (e.key === "ArrowLeft"  || e.key === "ArrowUp")   { lbNavThumb(-1); return; }
      if (e.key === "Escape") { closeLightbox(); return; }
      return;
    }
    switch (e.key) {
      case "ArrowRight": case "ArrowDown":  navigate(1);  break;
      case "ArrowLeft":  case "ArrowUp":    navigate(-1); break;
      case "f": case "F": toggleFullscreen(); break;
      case "g": case "G": toggleOverview(); break;
      case "b": case "B": toggleSidebar(); break;
      case "+": case "=": deckZoom(1);  break;
      case "-": case "_": deckZoom(-1); break;
      case "0": deckZoomReset(); break;
    }
  }

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

  // -- Lightbox (zoom/pan + thumbnails) -----------------------
  // Internal lightbox state
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
    var currentSlide = slides[current];
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

  // -- Image Slider ----------------------------------------
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

  // -- Sidebar toggle & resize ----------------------------
  var _sbMinWidth = 120;
  var _sbMaxWidth = 480;

  function initSidebar() {
    var saved = localStorage.getItem("tessera-sb-width");
    if (saved) {
      var w = parseInt(saved, 10);
      if (w >= _sbMinWidth && w <= _sbMaxWidth) {
        _savedSidebarWidth = w + "px";
        document.documentElement.style.setProperty("--sidebar-width", _savedSidebarWidth);
      }
    }
    // Reconcile collapse state. A remembered toggle (localStorage) wins over
    // the server-rendered default; otherwise the .sb-collapsed body class
    // (set when sidebar_collapsed=True) governs.
    var storedCollapsed = localStorage.getItem("tessera-sb-collapsed");
    if (storedCollapsed === "1") {
      document.documentElement.style.setProperty("--sidebar-width", "0px");
      document.body.classList.add("sb-collapsed");
    } else if (storedCollapsed === "0") {
      document.body.classList.remove("sb-collapsed");
      document.documentElement.style.setProperty("--sidebar-width", _savedSidebarWidth);
    }

    var handle = document.getElementById("sidebar-resize-handle");
    if (!handle) return;

    handle.addEventListener("mousedown", function (e) {
      if (e.button !== 0) return;
      e.preventDefault();
      handle.classList.add("dragging");
      document.body.classList.add("sb-no-transition");

      function onMove(e) {
        var w = Math.max(_sbMinWidth, Math.min(_sbMaxWidth, e.clientX));
        document.documentElement.style.setProperty("--sidebar-width", w + "px");
      }

      function onUp() {
        handle.classList.remove("dragging");
        document.body.classList.remove("sb-no-transition");
        var w = getComputedStyle(document.documentElement)
          .getPropertyValue("--sidebar-width").trim();
        _savedSidebarWidth = w;
        localStorage.setItem("tessera-sb-width", parseInt(w, 10));
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
      }

      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    });
  }

  // Flags the deck area to hide its scrollbars (see layout.css) for the duration
  // of the sidebar width transition, so they don't flicker mid-animation.
  var _sbAnimTimer = null;
  function markSidebarAnimating() {
    document.body.classList.add("sb-animating");
    if (_sbAnimTimer) clearTimeout(_sbAnimTimer);
    _sbAnimTimer = setTimeout(function () {
      document.body.classList.remove("sb-animating");
      _sbAnimTimer = null;
    }, 240);   // slightly longer than the 0.2s width/left transition
  }

  function toggleSidebar() {
    var collapsed = document.body.classList.toggle("sb-collapsed");
    if (collapsed) {
      var current = getComputedStyle(document.documentElement)
        .getPropertyValue("--sidebar-width").trim();
      if (parseInt(current, 10) > 0) _savedSidebarWidth = current;
      document.documentElement.style.setProperty("--sidebar-width", "0px");
    } else {
      document.documentElement.style.setProperty("--sidebar-width", _savedSidebarWidth);
    }
    markSidebarAnimating();
    localStorage.setItem("tessera-sb-collapsed", collapsed ? "1" : "0");
  }

  // -- Sidebar search & collapsible sections --------------
  var _collapsedSections = new Set();
  var _searchActive = false;
  var _searchRe = null;
  var _regexMode = false;          // literal by default; remembered across reloads
  var _ancestors = new Map();      // item el -> [ancestor section id, ...] (outermost first)
  var _sectionGroups = new Map();  // section id -> [descendant item els]
  var _searchTimer = null;
  var SB_COLLAPSED_KEY = "tessera-sb-collapsed-sections";
  var SB_REGEX_KEY = "tessera-sb-regex";

  function initSidebarSections() {
    if (!document.getElementById("slide-list")) return;   // chromeless / no sidebar
    buildSectionTree();
    hideEmptyCarets();
    restoreCollapsed();
    restoreRegexMode();
    applySidebarVisibility();
    // Hide the fold toolbar when the deck has no foldable sections.
    var foldBar = document.getElementById("sidebar-fold-bar");
    if (foldBar && _sectionEls().length === 0) foldBar.style.display = "none";
  }

  // Foldable sections (those with a non-empty descendant group), with level.
  function _sectionEls() {
    var out = [];
    document.querySelectorAll('.sidebar-item[data-type="section"]').forEach(function (el) {
      var group = _sectionGroups.get(el.dataset.target);
      if (group && group.length) {
        out.push({ el: el, id: el.dataset.target, level: parseInt(el.dataset.level, 10) || 0 });
      }
    });
    return out;
  }

  function _applyFold(touched) {
    touched.forEach(syncCaret);
    persistCollapsed();
    applySidebarVisibility();
  }

  function collapseAllSections() {
    var touched = [];
    _sectionEls().forEach(function (s) {
      if (!_collapsedSections.has(s.id)) { _collapsedSections.add(s.id); touched.push(s.id); }
    });
    _applyFold(touched);
  }

  function expandAllSections() {
    var touched = Array.from(_collapsedSections);
    _collapsedSections.clear();
    _applyFold(touched);
  }

  // Progressive: fold the deepest currently-open layer of sections.
  function collapseLevel() {
    var open = _sectionEls().filter(function (s) {
      return !_collapsedSections.has(s.id) && !hasCollapsedAncestor(s.el);
    });
    if (!open.length) return;
    var maxLevel = open.reduce(function (m, s) { return Math.max(m, s.level); }, 0);
    var touched = [];
    open.forEach(function (s) {
      if (s.level === maxLevel) { _collapsedSections.add(s.id); touched.push(s.id); }
    });
    _applyFold(touched);
  }

  // Progressive: reveal the outermost currently-folded layer of sections.
  function expandLevel() {
    var folded = _sectionEls().filter(function (s) {
      return _collapsedSections.has(s.id) && !hasCollapsedAncestor(s.el);
    });
    if (!folded.length) return;
    var minLevel = folded.reduce(function (m, s) { return Math.min(m, s.level); }, Infinity);
    var touched = [];
    folded.forEach(function (s) {
      if (s.level === minLevel) { _collapsedSections.delete(s.id); touched.push(s.id); }
    });
    _applyFold(touched);
  }

  // Walk the flat item list with a level stack to derive each item's ancestor
  // sections. A section records its ancestors before pushing itself, so it is
  // never its own ancestor; popping while top.level >= level means a level-1
  // section's group spans nested level-2 subsections (level-based nesting).
  function buildSectionTree() {
    var items = Array.from(document.querySelectorAll(".sidebar-item"));
    var stack = [];  // [{id, level}]
    items.forEach(function (el) {
      var type = el.dataset.type;
      var level = parseInt(el.dataset.level, 10) || 0;
      if (type === "section") {
        while (stack.length && stack[stack.length - 1].level >= level) stack.pop();
      }
      var anc = stack.map(function (s) { return s.id; });
      _ancestors.set(el, anc);
      anc.forEach(function (id) {
        if (!_sectionGroups.has(id)) _sectionGroups.set(id, []);
        _sectionGroups.get(id).push(el);
      });
      if (type === "section") stack.push({ id: el.dataset.target, level: level });
    });
  }

  function hideEmptyCarets() {
    document.querySelectorAll('.sidebar-item[data-type="section"]').forEach(function (el) {
      var group = _sectionGroups.get(el.dataset.target);
      var caret = el.querySelector(".sidebar-caret");
      if (caret && (!group || group.length === 0)) caret.classList.add("sidebar-caret-empty");
    });
  }

  // -- Search --------------------------------------------
  function filterSidebar(value) {
    // Debounce so content-scope search stays responsive on large decks.
    if (_searchTimer) clearTimeout(_searchTimer);
    _searchTimer = setTimeout(function () { _applyFilter(value); }, 120);
  }

  function escapeRegex(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function _applyFilter(value) {
    var input = document.getElementById("sidebar-search");
    value = (value || "").trim();
    if (value === "") {
      _searchActive = false; _searchRe = null;
      if (input) input.classList.remove("sidebar-search-error");
    } else if (_regexMode) {
      try {
        _searchRe = new RegExp(value, "i");
        _searchActive = true;
        if (input) input.classList.remove("sidebar-search-error");
      } catch (e) {
        _searchRe = null; _searchActive = false;   // invalid regex -> no filter
        if (input) input.classList.add("sidebar-search-error");
      }
    } else {
      // Literal mode: escape the query so specials match verbatim (always valid).
      _searchRe = new RegExp(escapeRegex(value), "i");
      _searchActive = true;
      if (input) input.classList.remove("sidebar-search-error");
    }
    applySidebarVisibility();
  }

  function _syncRegexUI() {
    var btn = document.getElementById("sidebar-regex-toggle");
    var wrap = document.getElementById("sidebar-search-wrap");
    var input = document.getElementById("sidebar-search");
    if (btn) btn.classList.toggle("active", _regexMode);
    if (wrap) wrap.classList.toggle("regex-on", _regexMode);
    if (input) input.placeholder = _regexMode ? "Filter slides… (regex)" : "Filter slides…";
  }

  function toggleRegexMode() {
    _regexMode = !_regexMode;
    try { localStorage.setItem(SB_REGEX_KEY, _regexMode ? "1" : "0"); } catch (e) {}
    _syncRegexUI();
    var input = document.getElementById("sidebar-search");
    if (input) _applyFilter(input.value);   // re-run with the new interpretation
  }

  function restoreRegexMode() {
    _regexMode = localStorage.getItem(SB_REGEX_KEY) === "1";
    _syncRegexUI();
    var input = document.getElementById("sidebar-search");
    if (input && input.value) _applyFilter(input.value);   // honor a restored value
  }

  function getSearchHaystack(el) {
    var scope = document.body.dataset.sbSearchScope || "title";
    var t = el.querySelector(".sidebar-title");
    var title = t ? t.textContent : "";
    if (scope === "title_subtitle") return title + " " + (el.dataset.subtitle || "");
    if (scope === "content") {
      var slide = document.getElementById(el.dataset.target);
      return title + " " + (slide ? slide.textContent : "");
    }
    return title;
  }

  function matchesSearch(el) {
    if (!_searchActive || !_searchRe) return true;
    return _searchRe.test(getSearchHaystack(el));
  }

  // -- Collapse ------------------------------------------
  function toggleSection(event, sectionId) {
    if (event) event.stopPropagation();
    if (_collapsedSections.has(sectionId)) _collapsedSections.delete(sectionId);
    else _collapsedSections.add(sectionId);
    persistCollapsed();
    syncCaret(sectionId);
    applySidebarVisibility();
  }

  function syncCaret(sectionId) {
    var sec = document.querySelector('.sidebar-item[data-target="' + cssEscape(sectionId) + '"]');
    var caret = sec && sec.querySelector(".sidebar-caret");
    if (caret) caret.classList.toggle("collapsed", _collapsedSections.has(sectionId));
  }

  function cssEscape(s) {
    return (window.CSS && CSS.escape) ? CSS.escape(s) : String(s).replace(/["\\]/g, "\\$&");
  }

  function persistCollapsed() {
    try {
      localStorage.setItem(SB_COLLAPSED_KEY, JSON.stringify(Array.from(_collapsedSections)));
    } catch (e) {}
  }

  function restoreCollapsed() {
    try {
      var raw = localStorage.getItem(SB_COLLAPSED_KEY);
      if (raw) {
        var arr = JSON.parse(raw);
        if (Array.isArray(arr)) arr.forEach(function (id) { _collapsedSections.add(id); });
      }
    } catch (e) {}
    _collapsedSections.forEach(function (id) { syncCaret(id); });
  }

  function hasCollapsedAncestor(el) {
    var anc = _ancestors.get(el) || [];
    for (var i = 0; i < anc.length; i++) if (_collapsedSections.has(anc[i])) return true;
    return false;
  }

  // Single source of truth: search overrides collapse while a query is active.
  function applySidebarVisibility() {
    var items = document.querySelectorAll(".sidebar-item");
    if (!items.length) return;
    items.forEach(function (el) {
      var visible = _searchActive ? matchesSearch(el) : !hasCollapsedAncestor(el);
      el.classList.toggle("sidebar-hidden", !visible);
    });
  }

  // Auto-expand collapsed ancestors of the active item so keyboard/arrow nav
  // into a folded section reveals it. Called at the end of goTo().
  function revealActiveSidebarItem() {
    if (_searchActive) return;   // search shows matches regardless of collapse
    var items = document.querySelectorAll(".sidebar-item");
    var el = items[current];
    if (!el) return;
    var anc = _ancestors.get(el) || [];
    var changed = false;
    anc.forEach(function (id) {
      if (_collapsedSections.has(id)) { _collapsedSections.delete(id); syncCaret(id); changed = true; }
    });
    if (changed) {
      persistCollapsed();
      if (!_searchActive) applySidebarVisibility();
      el.scrollIntoView({ block: "nearest" });   // re-scroll now that it is shown
    }
  }

  // -- Copy -----------------------------------------------
  function copyCell(btn) {
    var cell = btn.closest(".cell");
    var body = cell && cell.querySelector(".cell-body");
    if (!body) return;
    var text = body.innerText || body.textContent || "";
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).catch(function() {});
    }
  }

  function _flashAction(btn, ok) {
    if (!btn) return;
    var prev = btn.innerHTML;
    btn.innerHTML = ok ? "&#10003;" : "&#10007;";
    setTimeout(function() { btn.innerHTML = prev; }, 1100);
  }

  /**
   * Copy a figure / image cell's picture to the clipboard as a PNG. Works for
   * <img> data URIs (PNG/WebP/SVG) and inline-SVG matplotlib figures by drawing
   * onto a canvas. Falls back to copying the src URL as text (e.g. a tainted
   * cross-origin remote image that can't be read back from the canvas).
   */
  function copyImage(btn) {
    var cell = btn.closest(".cell");
    if (!cell) return;
    // For a slider, copy the currently visible slide; otherwise the cell image.
    var el = null;
    var sliderImgs = cell.querySelectorAll(".slider-img");
    sliderImgs.forEach(function(img) { if (!el && img.offsetParent !== null) el = img; });
    if (!el) {
      el = cell.querySelector("img.cell-img")
        || cell.querySelector(".matplotlib-svg")
        || cell.querySelector("img, svg");
    }
    var src = _imgSrc(el);
    if (!src) return;

    var canCopyImg = navigator.clipboard && window.ClipboardItem;
    if (!canCopyImg) {
      if (navigator.clipboard) {
        navigator.clipboard.writeText(src).then(function() { _flashAction(btn, true); },
                                               function() { _flashAction(btn, false); });
      }
      return;
    }

    var img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = function() {
      try {
        var canvas = document.createElement("canvas");
        canvas.width = img.naturalWidth || img.width || 1;
        canvas.height = img.naturalHeight || img.height || 1;
        canvas.getContext("2d").drawImage(img, 0, 0);
        canvas.toBlob(function(blob) {
          if (!blob) { _flashAction(btn, false); return; }
          navigator.clipboard.write([new ClipboardItem({ "image/png": blob })])
            .then(function() { _flashAction(btn, true); },
                  function() { _flashAction(btn, false); });
        }, "image/png");
      } catch (e) {
        // Canvas tainted (cross-origin) — fall back to copying the URL.
        navigator.clipboard.writeText(src).then(function() { _flashAction(btn, true); },
                                               function() { _flashAction(btn, false); });
      }
    };
    img.onerror = function() {
      navigator.clipboard.writeText(src).then(function() { _flashAction(btn, true); },
                                             function() { _flashAction(btn, false); });
    };
    img.src = src;
  }

  // -- Plotly ----------------------------------------------
  // Pull text/grid colours from the active theme's CSS variables so Plotly
  // stays legible on light themes (where the old hardcoded light-grey font was
  // invisible). Axes inherit the font colour and a muted grid colour.
  function _plotlyThemeColors() {
    var cs = getComputedStyle(document.body);
    var text = (cs.getPropertyValue("--color-text") || "").trim() || "#eaeaea";
    var grid = (cs.getPropertyValue("--color-border") || "").trim() || "rgba(128,128,128,.3)";
    return { text: text, grid: grid };
  }

  function initPlotlyCharts() {
    if (typeof Plotly === "undefined") return;
    var c = _plotlyThemeColors();
    var axis = { gridcolor: c.grid, zerolinecolor: c.grid, linecolor: c.grid };
    var containers = document.querySelectorAll(".plotly-container");
    containers.forEach(function(el) {
      try {
        var raw = el.getAttribute("data-fig");
        if (!raw) return;
        var fig = JSON.parse(raw);
        var base = fig.layout || {};
        var layout = Object.assign({}, base, {
          paper_bgcolor: "rgba(0,0,0,0)",
          plot_bgcolor:  "rgba(0,0,0,0)",
          font: Object.assign({ color: c.text }, base.font || {}, { color: c.text }),
          xaxis: Object.assign({}, axis, base.xaxis || {}),
          yaxis: Object.assign({}, axis, base.yaxis || {}),
          margin: { t: 30, r: 10, b: 40, l: 50 },
          autosize: true,
        });
        Plotly.newPlot(el, fig.data || [], layout, { responsive: true });
      } catch(e) {
        el.textContent = "Error rendering chart: " + e.message;
      }
    });
  }

  function renderMermaidInSlide(slideEl) {
    if (typeof mermaid === "undefined") return;
    var unprocessed = Array.from(slideEl.querySelectorAll("pre.mermaid")).filter(function(el) {
      return !el.getAttribute("data-processed");
    });
    if (unprocessed.length > 0) {
      mermaid.run({ nodes: unprocessed });
    }
  }

  function resizePlotlyInSlide(slideEl) {
    if (typeof Plotly === "undefined") return;
    var containers = slideEl.querySelectorAll(".plotly-container");
    containers.forEach(function(el) {
      if (el._fullLayout) Plotly.relayout(el, { autosize: true });
    });
  }

  // -- Tabulator -------------------------------------------
  // Build each interactive table the first time its slide is shown (so it is
  // measured while visible, not inside a display:none slide), then redraw on
  // every (re)activation and on resize to track the fixed-size stage scale.

  var _tabulatorFormatsReady = false;
  function ensureTabulatorFormats() {
    if (_tabulatorFormatsReady || typeof Tabulator === "undefined") return;
    _tabulatorFormatsReady = true;
    Tabulator.extendModule("format", "formatters", {
      // Continuous row numbers across paginated pages.
      // getPosition(true) returns the row's 1-based index in the full filtered
      // set (post-filter, post-sort, before pagination slicing), so the counter
      // never resets when the reader flips to a new page.
      rownumGlobal: function(cell) {
        try {
          var pos = cell.getRow().getPosition(true);
          return pos !== false ? pos : "";
        } catch(e) { return ""; }
      }
    });
  }

  function buildTabulator(el) {
    if (el._tbBuilt || typeof Tabulator === "undefined") return;
    ensureTabulatorFormats();
    var cfgEl = document.getElementById(el.id + "-cfg");
    if (!cfgEl) return;
    el._tbBuilt = true;
    try {
      var table = new Tabulator(el, JSON.parse(cfgEl.textContent));
      el._tabulator = table;
      var card = el.closest(".cell");
      if (card) {
        card.querySelectorAll("[data-tab-download]").forEach(function(b) {
          b.addEventListener("click", function() {
            var f = b.getAttribute("data-tab-download");
            table.download(f, "data." + f);
          });
        });
      }
    } catch (e) {
      el.textContent = "Error rendering table: " + e.message;
    }
  }

  function renderTabulatorsInSlide(slideEl) {
    if (typeof Tabulator === "undefined") return;
    slideEl.querySelectorAll(".tessera-tabulator").forEach(function(el) {
      buildTabulator(el);
      var t = el._tabulator;
      // Defer the redraw so it runs after the stage transform / layout settles.
      if (t) requestAnimationFrame(function() { try { t.redraw(true); } catch (e) {} });
    });
  }

  function expandPlotly(btn) {
    expandCell(btn);
  }

  // -- Expose global functions ----------------------------
  window.toggleSidebar         = toggleSidebar;
  window.navigate              = navigate;
  window.goToSlide             = goToSlide;
  window.goToIndex             = goToIndex;
  window.toggleFullscreen      = toggleFullscreen;
  window.toggleOverview        = toggleOverview;
  window.expandCell            = expandCell;
  window.expandPlotly          = expandPlotly;
  window.closeModal            = closeModal;
  window.openLightbox          = openLightbox;
  window.openLightboxFromSlider = openLightboxFromSlider;
  window.closeLightbox         = closeLightbox;
  window.lbGoTo                = lbGoTo;
  window.lbNavThumb            = lbNavThumb;
  window.lbResetZoom           = lbResetZoom;
  window.copyCell              = copyCell;
  window.copyImage             = copyImage;
  window.sliderNav             = sliderNav;
  window.filterSidebar         = filterSidebar;
  window.toggleSection         = toggleSection;
  window.toggleRegexMode       = toggleRegexMode;
  window.collapseAllSections   = collapseAllSections;
  window.expandAllSections     = expandAllSections;
  window.collapseLevel         = collapseLevel;
  window.expandLevel           = expandLevel;
  window.deckZoom              = deckZoom;
  window.deckZoomReset         = deckZoomReset;

  // -- Boot -----------------------------------------------
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

})();
