/* montin — toolbar.js
   ----------------------------------------------------------------------------
   Keeps --toolbar-height in sync with the toolbar's real (possibly wrapped)
   height so #main / #sidebar reserve the right amount of space.

   T.state: none.   Calls: none.   Registers: T.initToolbar.
   ------------------------------------------------------------------------- */
(function (T) {
  "use strict";

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

  T.initToolbar = initToolbar;

})(window.Montin = window.Montin || {});
