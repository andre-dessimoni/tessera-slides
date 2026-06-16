/* tessera — main.js
   Navigation, fullscreen, overview, modal, lightbox (zoom/pan/thumbnails),
   image slider, plotly init.
   No external dependencies (Plotly is initialised if present).
*/

(function () {
  "use strict";

  // -- State -----------------------------------------------
  const slides = Array.from(document.querySelectorAll(".slide"));
  let current = 0;
  var _savedSidebarWidth = "220px";

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
    initStage();
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

    body.style.setProperty("--stage-sx", sx);
    body.style.setProperty("--stage-sy", sy);
  }

  function initStage() {
    if (!document.body.classList.contains("fixed-size")) return;
    fitStage();
    var main = document.getElementById("main");
    // ResizeObserver on #main captures window resizes (it is pinned to the
    // window edges) and sidebar toggle/resize (which shifts its left edge).
    if (main && "ResizeObserver" in window) {
      new ResizeObserver(fitStage).observe(main);
    } else {
      window.addEventListener("resize", fitStage);
    }
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
    revealActiveSidebarItem();
  }

  function navigate(delta) {
    goTo(current + delta);
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
   * Collects all images from the current slide (cell-image + sliders).
   * Returns [{src, alt}].
   */
  function _collectSlideImages() {
    var currentSlide = slides[current];
    if (!currentSlide) return [];
    var imgs = [];
    // Regular images (cell-image)
    currentSlide.querySelectorAll(".cell-image .lightbox-trigger").forEach(function(img) {
      imgs.push({ src: img.src, alt: img.alt || "" });
    });
    // Sliders: collect all images from each slider
    currentSlide.querySelectorAll(".cell-image-slider .slider-img").forEach(function(img) {
      imgs.push({ src: img.src, alt: img.alt || "" });
    });
    return imgs;
  }

  function openLightbox(imgEl) {
    _lb.images = _collectSlideImages();
    var src = imgEl.src;
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
    localStorage.setItem("tessera-sb-collapsed", collapsed ? "1" : "0");
  }

  // -- Sidebar search & collapsible sections --------------
  var _collapsedSections = new Set();
  var _searchActive = false;
  var _searchRe = null;
  var _ancestors = new Map();      // item el -> [ancestor section id, ...] (outermost first)
  var _sectionGroups = new Map();  // section id -> [descendant item els]
  var _searchTimer = null;
  var SB_COLLAPSED_KEY = "tessera-sb-collapsed-sections";

  function initSidebarSections() {
    if (!document.getElementById("slide-list")) return;   // chromeless / no sidebar
    buildSectionTree();
    hideEmptyCarets();
    restoreCollapsed();
    applySidebarVisibility();
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

  function _applyFilter(value) {
    var input = document.getElementById("sidebar-search");
    value = (value || "").trim();
    if (value === "") {
      _searchActive = false; _searchRe = null;
      if (input) input.classList.remove("sidebar-search-error");
    } else {
      try {
        _searchRe = new RegExp(value, "i");
        _searchActive = true;
        if (input) input.classList.remove("sidebar-search-error");
      } catch (e) {
        _searchRe = null; _searchActive = false;   // invalid regex -> no filter
        if (input) input.classList.add("sidebar-search-error");
      }
    }
    applySidebarVisibility();
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

  // -- Plotly ----------------------------------------------
  function initPlotlyCharts() {
    if (typeof Plotly === "undefined") return;
    var containers = document.querySelectorAll(".plotly-container");
    containers.forEach(function(el) {
      try {
        var raw = el.getAttribute("data-fig");
        if (!raw) return;
        var fig = JSON.parse(raw);
        var layout = Object.assign({}, fig.layout || {}, {
          paper_bgcolor: "rgba(0,0,0,0)",
          plot_bgcolor:  "rgba(0,0,0,0)",
          font: { color: "#eaeaea" },
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
  window.sliderNav             = sliderNav;
  window.filterSidebar         = filterSidebar;
  window.toggleSection         = toggleSection;

  // -- Boot -----------------------------------------------
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

})();
