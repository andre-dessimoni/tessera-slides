All notable changes to this project will be documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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

- **`add_matplotlib` now defaults to `fmt="svg"`** (was `"png"`) — crisp, vector,
  infinitely zoomable. Use `fmt="webp"`/`to_webp=True` for dense plots where SVG
  gets large.
- Plotly charts now read the active theme's CSS variables for text/grid colours,
  fixing invisible chart text on light themes.
- Arrow-key / prev-next navigation now steps into a collapsed section (auto-
  expanding it) instead of skipping over it; search-filtered slides are still
  skipped.

### Changed (breaking)

- **Renamed the PyPI distribution `tessera-slides` → `tessera-report`.** The
  import package is unchanged (`import tessera`). Install with
  `pip install tessera-report`. The old `tessera-slides` distribution continues
  to install a deprecation shim that depends on `tessera-report`.
- **Renamed the main class `HTMLSlides` → `Deck`** (no alias; update
  `from tessera import HTMLSlides` to `from tessera import Deck`). The internal
  module `tessera.core.slides` moved to `tessera.core.deck`.
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

