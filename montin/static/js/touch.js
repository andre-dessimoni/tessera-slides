/* montin — touch.js
   ----------------------------------------------------------------------------
   Touchscreen gestures on the deck: one-finger horizontal swipe to change slide
   (left -> next, right -> previous) and two-finger pinch to drive the deck zoom.
   Swipe only fires while the slide fits (<=100% zoom, no horizontal overflow) so
   a zoomed-in slide can still be panned natively. #main has touch-action:
   pan-x pan-y (layout.css) so the browser's own pinch/double-tap zoom is off and
   we can preventDefault here.

   T.state: reads deckZoom.
   Calls: T.navigate, T.applyDeckZoom, T.setDeckZoomLive.
   Registers: T.initTouchGestures.
   ------------------------------------------------------------------------- */
(function (T) {
  "use strict";

  var _touch = { startX: 0, startY: 0, swiping: false,
                 pinching: false, startDist: 0, startZoom: 1, lockedAfterPinch: false };
  var SWIPE_MIN = 50; // px of horizontal travel to count as a swipe

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
      _touch.startZoom = T.state.deckZoom;
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
        if (T.state.deckZoom > 1 || main.scrollWidth > main.clientWidth + 1) return;
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
        T.setDeckZoomLive(_touch.startZoom * ratio);
        e.preventDefault();
      }
    }, { passive: false });

    function onEnd(e) {
      if (_touch.swiping) {
        var t = e.changedTouches[0];
        var dx = t.clientX - _touch.startX;
        var dy = t.clientY - _touch.startY;
        if (Math.abs(dx) >= SWIPE_MIN && Math.abs(dx) > Math.abs(dy) * 1.5) {
          T.navigate(dx < 0 ? 1 : -1); // swipe left -> next, swipe right -> previous
        }
        _touch.swiping = false;
      }
      if (_touch.pinching && e.touches.length < 2) {
        _touch.pinching = false;
        _touch.lockedAfterPinch = true; // ignore the leftover finger as a swipe
        T.applyDeckZoom(); // finalize with the full (table re-render) path
      }
      if (e.touches.length === 0) {
        _touch.lockedAfterPinch = false;
      }
    }
    main.addEventListener("touchend", onEnd, { passive: true });
    main.addEventListener("touchcancel", onEnd, { passive: true });
  }

  T.initTouchGestures = initTouchGestures;

})(window.Montin = window.Montin || {});
