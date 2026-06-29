"""
montin.utils.theme_resolver
==============================
Resolves and merges CSS files per component following the hierarchy:
  1. default/
  2. user-chosen theme
  3. custom_css provided via Python
"""
from __future__ import annotations

from pathlib import Path

from montin.utils.resource_loader import (
    get_theme_file, theme_file_exists, get_available_themes)

#: CSS components recognised by the theme system.
CSS_COMPONENTS = [
    "image",
    "layout",
    "slide",
    "table",
    "tabulator",
    "list",
    "toc",
    "code",
    "metric",
    "toolbar",
]


class ThemeResolver:
    def resolve(
        self,
        theme: str,
        custom_css: Path | None = None,
    ) -> str:
        """
        Returns a single CSS string with all components merged.
        Hierarchy: default → theme → custom_css.
        """
        from montin.exceptions import ThemeNotFoundError

        parts: list[str] = []

        for component in CSS_COMPONENTS:
            filename = f"{component}.css"

            # 1. default
            default_path = get_theme_file("default", filename)
            if default_path.exists():
                parts.append(f"/* --- default/{filename} --- */")
                parts.append(default_path.read_text(encoding="utf-8"))

            # 2. chosen theme (overrides if present)
            if theme != "default":
                theme_dir = get_theme_file(theme, "layout.css").parent
                if not theme_dir.exists():
                    raise ThemeNotFoundError(
                        f"Theme '{theme}' not found. "
                        f"Expected folder: {theme_dir}"
                        f"\nAvailable themes:\n-"
                        + '\n-'.join([f.name for f in get_available_themes()])
                    )
                if theme_file_exists(theme, filename):
                    parts.append(f"/* --- {theme}/{filename} --- */")
                    parts.append(
                        get_theme_file(theme, filename).read_text(encoding="utf-8")
                    )

        # 3. user custom_css
        if custom_css is not None:
            if isinstance(custom_css, Path) and custom_css.exists():
                parts.append("/* --- custom_css --- */")
                parts.append(custom_css.read_text(encoding="utf-8"))
            elif isinstance(custom_css, str):
                parts.append("/* --- custom_css (inline) --- */")
                parts.append(custom_css)

        return "\n".join(parts)
