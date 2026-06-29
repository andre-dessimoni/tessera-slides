# Deck JavaScript — architecture

The deck's client-side behavior lives in this folder, split into small,
feature-focused modules. At build time the assembler (`montin/core/assembler.py`)
reads them **in a fixed order**, concatenates them, and inlines the result into the
report's single
`<script>` block (see `MAIN_JS_MODULES` in `montin/core/assembler.py`). There is
**no bundler and no build step** — the project ships plain `.js` that is read and
inlined at render time.

## Why this design

The report is a single self-contained HTML file: all JS is inlined into one
`<script>`. That rules out native ES modules (`import`/`export` between inline
scripts needs separate URLs or a bundler), and adding a Node toolchain (esbuild,
rollup) would be a heavy dependency for a pure-Python package.

We also can't just drop each feature into its own independent IIFE: the features
are tightly coupled. They share mutable state (the active slide index, the deck
zoom) and call across each other constantly (navigation triggers chart/table
rendering and sidebar reveal; the keyboard handler drives navigation, zoom,
fullscreen, sidebar, lightbox; touch drives navigation and zoom). Independent
closures couldn't see each other's state or functions.

The solution is a **shared namespace**: one global object, `window.Montin`
(aliased `T` inside each module), carries the shared state and the cross-module
API. Each module is its own IIFE that reads/writes that object.

## The `Montin` (`T`) contract

Three places things can live — pick the narrowest that works:

- **`T.state`** — shared *mutable* state read or written by more than one module.
  Today: `slides`, `current`, `deckZoom`, `searchActive` (defined in `state.js`).
  Per-feature state (e.g. the lightbox's `_lb`, the sliders map, sidebar's
  collapse/search internals) stays a **local `var`** inside its module.
- **`T.<fn>`** — a function called from *another* module. Register it at the
  bottom of the module: `T.goTo = goTo;`. Functions used only inside their own
  module stay local (no `T.`).
- **`window.<fn>`** — the HTML-facing API. Templates call these bare from inline
  `onclick="navigate(1)"` etc. `boot.js` mirrors them from `T` onto `window`.

Rule of thumb: **local-only stays local; cross-called gets registered on `T`;
HTML-called also gets mirrored onto `window` (in `boot.js`).**

Each module starts with a header comment listing which `T.state` fields it
touches, which `T.*` functions it calls (its dependencies), and what it registers.

## Load order

`state.js` **first** (creates `window.Montin` and `T.state`), `boot.js` **last**
(every module has registered by then; it wires listeners, runs the `init*`
sequence, mirrors the `window` API, and boots on DOM-ready). The order between is
the `MAIN_JS_MODULES` list:

```
state, toolbar, stage, zoom, navigation, keyboard, view,
lightbox, slider, sidebar, copy, charts, touch, boot
```

Registration happens when each module's IIFE runs; cross-module calls happen later
(events, `init`), so the in-between order is not load-sensitive — only "state
first, boot last" matters.

## Adding a new module

1. Create `js/<name>.js` using the standard wrapper:
   ```js
   (function (T) {
     "use strict";
     // ... feature code; local state as local vars ...
     T.myPublicFn = myPublicFn;   // only if another module calls it
   })(window.Montin = window.Montin || {});
   ```
2. Add `"<name>"` to `MAIN_JS_MODULES` in `montin/core/assembler.py` (mind the
   "state first / boot last" rule).
3. If the feature is invoked from a template's `onclick`, mirror it onto `window`
   in `boot.js`.
4. New files in this directory are already packaged by the `static/js/*.js` glob
   in `pyproject.toml` — no change needed unless you add a subdirectory.
