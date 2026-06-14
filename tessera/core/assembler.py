"""
tessera.core.assembler
=======================
Consumes a populated ``HTMLSlides`` instance and writes the final .html file.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import jinja2
from importlib.resources import files as _res_files

from tessera.cells import ImageCell, ImageSliderCell
from tessera.utils.theme_resolver import ThemeResolver

if TYPE_CHECKING:
    from tessera.core.slides import HTMLSlides


def _templates_dir() -> Path:
    return Path(str(_res_files("tessera.templates")))


def _static_dir() -> Path:
    return Path(str(_res_files("tessera.static")))


class Assembler:
    def __init__(self, deck: "HTMLSlides") -> None:
        self.deck = deck
        self._env = self._build_jinja_env()

    def write(self, path: Path) -> None:
        html = self._render()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")

    def _build_jinja_env(self) -> jinja2.Environment:
        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(_templates_dir())),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _render(self) -> str:
        deck = self.deck

        # CSS — theme merge
        css = ThemeResolver().resolve(deck.theme, deck.custom_css)

        # Main JS
        js_path = _static_dir() / "main.js"
        main_js = js_path.read_text(encoding="utf-8") if js_path.exists() else ""

        # Resolve ImageCell.resolved_src (base64 if self_contained, otherwise src as-is)
        if deck.self_contained:
            from tessera.utils.image_encoder import encode
            for slide in deck._slides:
                for cell in slide._cells:
                    if isinstance(cell, ImageCell) and not cell.resolved_src:
                        try:
                            cell.resolved_src = encode(cell.source)
                        except FileNotFoundError:
                            cell.resolved_src = str(cell.source)
                    elif isinstance(cell, ImageSliderCell) and not cell.resolved_srcs:
                        srcs = []
                        for s in cell.sources:
                            try:
                                srcs.append(encode(s))
                            except FileNotFoundError:
                                srcs.append(str(s))
                        cell.resolved_srcs = srcs
        else:
            for slide in deck._slides:
                for cell in slide._cells:
                    if isinstance(cell, ImageCell) and not cell.resolved_src:
                        cell.resolved_src = str(cell.source)
                    elif isinstance(cell, ImageSliderCell) and not cell.resolved_srcs:
                        cell.resolved_srcs = [str(s) for s in cell.sources]

        # Build full TOC from registered sections
        toc_entries = [
            {
                "title":    s["title"],
                "subtitle": s.get("subtitle", ""),
                "level":    s["level"],
                "slide_id": s["slide_id"],
            }
            for s in deck._sections
        ]

        # Render cells + inject TOC entries per slide
        rendered_slides = []
        for slide in deck._slides:
            entries_for_template: list[dict] = []

            if slide.slide_type == "toc":
                auto = getattr(slide, "_auto_toc", True)
                slide._toc_entries = toc_entries if auto else []
                entries_for_template = list(slide._toc_entries)

            elif slide.slide_type == "section" and slide.show_toc and toc_entries:
                current_id = slide.slide_id
                current_idx = next(
                    (i for i, e in enumerate(toc_entries) if e["slide_id"] == current_id),
                    -1,
                )
                slide._toc_entries = toc_entries
                entries_for_template = [
                    {
                        **e,
                        "is_current":  i == current_idx,
                        "is_past":     i < current_idx,
                        "is_upcoming": i > current_idx,
                    }
                    for i, e in enumerate(toc_entries)
                ]

            rendered_cells = [cell.render(self._env) for cell in slide._cells]
            rendered_slides.append({
                "slide":          slide,
                "rendered_cells": rendered_cells,
                "toc_entries":    entries_for_template,
            })

        return self._env.get_template("base.html").render(
            deck=deck,
            rendered_slides=rendered_slides,
            css=css,
            main_js=main_js,
            plugins=deck.plugins,
            plugin_names=deck._plugin_names,
        )
