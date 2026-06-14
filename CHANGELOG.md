All notable changes to this project will be documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-06-14

### Added

- `slide_id` and `cell_id` arguments to avoid duplicating slides and cells while
  re-running code-cells on interactive Jupyter notebooks.

- `auto_save` and `auto_save_level` options to help creating presentations on 
  interactive Jupyter notebooks, without having to call `.write()` manually.

- `get_slide` to retrieve an slide.

- All cells now have a `__repr__` method to help identifying them.

