/* montin — copy.js
   ----------------------------------------------------------------------------
   Copy-to-clipboard for cells: text bodies, and figure/image cells rendered to
   a PNG (with graceful fallbacks to copying the src URL).

   T.state: none.   Calls: T._imgSrc (shared image-src helper from lightbox.js).
   Registers: T.copyCell, T.copyImage.
   ------------------------------------------------------------------------- */
(function (T) {
  "use strict";

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
    var src = T._imgSrc(el);
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

  T.copyCell  = copyCell;
  T.copyImage = copyImage;

})(window.Montin = window.Montin || {});
