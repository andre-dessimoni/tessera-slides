All notable changes to this project will be documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2026-06-22

### Added

- **Font scaling.** `Deck(fontsize_scale=…)` scales every font in the
  presentation — slide content and navigation chrome alike — by one factor,
  leaving spacing/layout untouched. Per-cell `slide.add_*(…, fontscale=…)` (and
  `CellDefaults(fontscale=…)`) scales a single cell's text and composes on top of
  the deck factor.
- **Interactive tables — `slide.add_tabulator()`** (new `Plugins.Tabulator()`),
  backed by the bundled [Tabulator](https://tabulator.info) library (MIT). Sort,
  filter, paginate, group, edit inline, and download (CSV/JSON). Takes the same
  inputs as `add_table` — and both now also accept a **path to a CSV/TSV file**.
  Per-column formatters/editors/calcs go through `columns=[...]`; the full
  Tabulator option set is reachable via `options={...}`. Two stock themes are
  vendored (light + dark); styling follows the deck theme automatically
  (`Plugins.Tabulator(theme="auto"|"light"|"dark")`). Works offline /
  under `Security(block_external=True)`.
- **Bundled (offline) plugins.** Each plugin can load from a CDN (`source="cdn"`,
  default) or be embedded in the report (`source="bundled"`) so it works with no
  network at all. Flip the whole deck with `Deck(plugin_source="bundled")`. The
  embedded libraries are vendored under `tessera/static/vendor/<library>/` — each
  alongside its `LICENSE` (Plotly/Mermaid MIT, highlight.js BSD-3-Clause, MathJax
  Apache-2.0) — and refreshed by the dev script `scripts/update_vendor.py` (which
  fetches code + licenses, with a `--check` mode and an update log).
- **Per-plugin classes via the `Plugins` container** — `Plugins.Plotly()`,
  `Plugins.Mermaid(theme=...)`, `Plugins.Highlight(style=...)`,
  `Plugins.MathJax(output=...)` — each with its own typed options, plus
  `version=` / `url=` / `set_cdn()` to pin a version or point at a custom mirror.
- **`Security(...)` hardening**, passed as `Deck(security=...)`. Light hardening is
  on by default (`no-referrer`, `Permissions-Policy`, and Subresource-Integrity on
  CDN libraries). `block_external=True` is a hard offline guarantee: it forces all
  plugins to bundle, emits a strict Content-Security-Policy, and raises
  `SecurityError` if the rendered report still references any external resource.
  New docs: *Plugins* and *Security & offline use*.
- `notebook_unique=True` on `add_slide`/`add_title`/`add_section`/`add_toc` and
  every cell `add_*`: re-running the *same* Jupyter cell replaces the items it
  created instead of duplicating them — no manual id needed. Keys off the Jupyter
  cell id; warns (and falls back) in a script, errors in an interactive session
  that can't supply one.
- `Deck(preview_height=...)` to set the notebook `_repr_html_` iframe height,
  propagated to slide and cell previews.
- WebP support for images and figures: `to_webp=True` / `webp_quality=` on
  `add_image`, `add_matplotlib`, `add_image_slider` (requires the new optional
  `pillow` dependency: `pip install 'tessera-report[image]'`).
- Contents folder: `Deck(contents_folder=...)` plus `save_source=True` on the
  media `add_*` (incl. `add_plotly`, which exports a standalone HTML). Saves
  assets to `_<report>_contents/` (created lazily). When the deck is
  self-contained the asset is still embedded *and* saved; otherwise the cell
  references the saved file.
- `add_image` and `add_image_slider` now accept matplotlib `Figure` objects
  (routed through the matplotlib pipeline).

### Changed

- **Optional-dependency extras now cover only what tessera itself imports.**
  `[full]` is `markdown-it-py` + `pillow`; the standalone `[plotly]` and
  `[pandas]` extras were removed. You build `Figure`/`DataFrame` objects yourself,
  so those libraries are already present when you call `add_plotly`/`add_table`/
  `add_matplotlib` — they're now pulled only by `[dev]` for the test suite.
- **`add_matplotlib` now defaults to `fmt="svg"`** (was `"png"`) — crisp, vector,
  infinitely zoomable. Use `fmt="webp"`/`to_webp=True` for dense plots where SVG
  gets large.
- Plotly charts now read the active theme's CSS variables for text/grid colours,
  fixing invisible chart text on light themes.
- Arrow-key / prev-next navigation now steps into a collapsed section (auto-
  expanding it) instead of skipping over it; search-filtered slides are still
  skipped.

### Fixed

- `add_*` cell methods now expose their real signatures to type checkers and
  editors (Pylance/pyright) instead of collapsing to `(...) -> Cell`. The
  `@cell_method` decorator is now signature-preserving (`ParamSpec`/`TypeVar`),
  so parameters and concrete return types show up in autocomplete and hovers.
- Title and section cover slides are now centered in fixed-size (`size=`) mode.
  The centering had relied on the `.slide` being the flex container, but in
  fixed-size mode that role moved to `.stage`, so covers rendered top-left;
  the cover now centers itself via `margin:auto`, working in both modes.

## [0.4.0] - 2026-06-17

### Changed (breaking)

- **Renamed the PyPI distribution `tessera-slides` → `tessera-report`.** The
  import package is unchanged (`import tessera`). Install with
  `pip install tessera-report`. The old `tessera-slides` distribution continues
  to install a deprecation shim that depends on `tessera-report`.
- **Renamed the main class `HTMLSlides` → `Deck`** (no alias; update
  `from tessera import HTMLSlides` to `from tessera import Deck`). The internal
  module `tessera.core.slides` moved to `tessera.core.deck`.
- **Replaced the flat `Plugin(name, source)` with the `Plugins.*` classes.**
  Update `Plugin("plotly", "cdn")` to `Plugins.Plotly(source="cdn")` (or just
  `Plugins.Plotly()` — the default source is now `"cdn"`). `Plugin` remains as the
  shared base type. Added `Deck(plugin_source=...)` to set the default for all
  plugins at once.
- Repositioned the library toward **self-contained, interactive HTML reports for
  batch-generated data/ML output** (was framed as "HTML slideshows").
- Fixed `__version__` resolution, which previously looked up the wrong
  distribution name and always fell back to `0.0.0.dev`.

### Added

- `_repr_html_` on `Deck`, `Slide`, and `Cell` for inline previews in
  Jupyter notebooks: return a deck, slide, or cell as a cell's last expression to
  render it in a sandboxed iframe (slide/cell previews are chrome-free and reuse
  the deck's theme and plugins).
- Sidebar fold toolbar: Collapse all / Expand all / Collapse level / Expand level
  buttons (shown when `sidebar_collapsible_sections` is on). The level buttons
  fold/unfold one nesting layer per click.
- Sidebar search regex toggle (literal matching by default; click `.*` to switch
  to regex), with a hover tooltip of common regex patterns while in regex mode.
  The chosen mode is remembered across reloads.

### Changed

- Sidebar arrow-key / prev-next navigation now steps only over *visible* items,
  skipping slides hidden by an active search filter or a collapsed section.
- Slightly enlarged the section fold caret for legibility.

## [0.3.0] - 2026-06-15

### Added

- `title_id`, `section_id`, and `toc_id` parameters on `add_title`, `add_section`,
  and `add_toc`, mirroring `slide_id` — re-running a notebook cell replaces the
  slide in place instead of appending a duplicate. Overwriting a section also
  updates its table-of-contents entry in place rather than duplicating it.
- Fixed-size "stage" mode: pass `size=(width, height)` to `Deck` to render
  slides at fixed pixel dimensions, scaled with a CSS transform to fit the window
  — fonts, images, and layout scale together like a static PDF. Options:
  `scale_up` (allow growing past 1:1) and `keep_aspect_ratio` (uniform letterbox
  vs. stretch-to-fill). Modal and lightbox stay unscaled.
- `show_sidebar` and `show_toolbar` options on `Deck` (both default
  `True`). Disable them for clean single-slide / embeddable files — e.g. the
  slides shown inline in the documentation.
- `sidebar_collapsed` option on `Deck` (default `False`) to start with the
  sidebar collapsed while keeping it toggleable. A remembered toggle state takes
  precedence over this default.
- Sidebar navigation aids: a regex **search box** that live-filters slides
  (`sidebar_search`, default `True`; `sidebar_search_scope` of `"title"` /
  `"title_subtitle"` / `"content"`) and **collapsible sections** with a fold
  caret on section items (`sidebar_collapsible_sections`, default `True`).
  Collapsed state is remembered across reloads; an active search overrides it.

### Fixed

- Overwriting a slide or cell by id now truly replaces it **in place** (keeping
  its position in the deck / grid), as the documentation already described;
  previously the replacement was moved to the end.
- The sidebar slide list now shows a vertical scrollbar when it overflows
  instead of clipping items.

## [0.2.0] - 2026-06-14

### Added

- `slide_id` and `cell_id` arguments to avoid duplicating slides and cells while
  re-running code-cells on interactive Jupyter notebooks.
- `auto_save` and `auto_save_level` options to help creating presentations on 
  interactive Jupyter notebooks, without having to call `.write()` manually.
- `get_slide` to retrieve an slide.
- All cells now have a `__repr__` method to help identifying them.
- Refactored the title and TOC features

