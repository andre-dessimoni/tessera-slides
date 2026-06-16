All notable changes to this project will be documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-06-15

### Added

- `title_id`, `section_id`, and `toc_id` parameters on `add_title`, `add_section`,
  and `add_toc`, mirroring `slide_id` — re-running a notebook cell replaces the
  slide in place instead of appending a duplicate. Overwriting a section also
  updates its table-of-contents entry in place rather than duplicating it.
- Fixed-size "stage" mode: pass `size=(width, height)` to `HTMLSlides` to render
  slides at fixed pixel dimensions, scaled with a CSS transform to fit the window
  — fonts, images, and layout scale together like a static PDF. Options:
  `scale_up` (allow growing past 1:1) and `keep_aspect_ratio` (uniform letterbox
  vs. stretch-to-fill). Modal and lightbox stay unscaled.
- `show_sidebar` and `show_toolbar` options on `HTMLSlides` (both default
  `True`). Disable them for clean single-slide / embeddable files — e.g. the
  slides shown inline in the documentation.
- `sidebar_collapsed` option on `HTMLSlides` (default `False`) to start with the
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

