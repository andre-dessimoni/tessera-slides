"""
tessera.utils.resource_loader
==============================
Locates package assets (templates, themes, static) via importlib.resources.
Works correctly in both installed and editable (pip install -e) modes.
"""

from __future__ import annotations

from pathlib import Path

try:
    from importlib.resources import files  # Python 3.9+
except ImportError:  # pragma: no cover
    from importlib_resources import files  # type: ignore[no-redef]


def get_template(name: str) -> Path:
    return Path(str(files("tessera.templates").joinpath(name)))


def get_theme_file(theme: str, filename: str) -> Path:
    return Path(str(files("tessera.themes").joinpath(theme, filename)))


def get_static(name: str) -> Path:
    return Path(str(files("tessera.static").joinpath(name)))


def theme_file_exists(theme: str, filename: str) -> bool:
    p = get_theme_file(theme, filename)
    return p.exists()

def get_available_themes() -> list:
    return list(filter(
        lambda f: f.is_dir() and not str(f.name).startswith('_'),
        Path(str(files("tessera.themes"))).glob('*')
    ))
