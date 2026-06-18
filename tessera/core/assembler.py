"""
tessera.core.assembler
=======================
Consumes a populated ``Deck`` instance and writes the final .html file.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import jinja2
from importlib.resources import files as _res_files

from tessera.cells import ImageCell, ImageSliderCell
from tessera.utils.theme_resolver import ThemeResolver

if TYPE_CHECKING:
    from tessera.core.deck import Deck


def _templates_dir() -> Path:
    return Path(str(_res_files("tessera.templates")))


def _static_dir() -> Path:
    return Path(str(_res_files("tessera.static")))


class Assembler:
    def __init__(self, deck: "Deck") -> None:
        self.deck = deck
        self._env = self._build_jinja_env()
        self._output_path: Path | None = None   # set by write(); None during previews

    def write(self, path: Path) -> None:
        self._output_path = Path(path)
        html = self._render()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")

    # ------------------------------------------------------------------
    # Media finalization (WebP conversion + contents-folder saving)
    # ------------------------------------------------------------------

    def _contents_dir(self) -> Path | None:
        """Folder for saved assets, or ``None`` during previews (no output path).

        Resolved to ``deck.contents_folder`` (relative to the output file when
        not absolute), else ``<output_dir>/_<output_stem>_contents``. The folder
        itself is created lazily, only when an asset is actually written.
        """
        out = self._output_path
        if out is None:
            return None
        cf = self.deck.contents_folder
        if cf is not None:
            cf = Path(cf)
            return cf if cf.is_absolute() else out.parent / cf
        return out.parent / f"_{out.stem}_contents"

    def _finalize_media(self) -> None:
        from tessera.cells.matplotlib import MatplotlibCell
        from tessera.cells.plotly import PlotlyCell
        contents_dir = self._contents_dir()
        out_dir = self._output_path.parent if self._output_path else None
        for slide in self.deck._slides:
            for cell in slide._cells:
                sid, cid = slide.slide_id, cell.params.cell_id
                if isinstance(cell, ImageCell):
                    if cell.resolved_src:
                        continue
                    cell.resolved_src = self._resolve_image(
                        cell.source, cell.to_webp, cell.webp_quality,
                        cell.save_source, contents_dir, out_dir, sid, cid, 0)
                elif isinstance(cell, ImageSliderCell):
                    if cell.resolved_srcs:
                        continue
                    cell.resolved_srcs = [
                        self._resolve_image(
                            s, cell.to_webp, cell.webp_quality, cell.save_source,
                            contents_dir, out_dir, sid, cid, i)
                        for i, s in enumerate(cell.sources)
                    ]
                elif isinstance(cell, MatplotlibCell):
                    self._finalize_matplotlib(cell, contents_dir, out_dir, sid, cid)
                elif isinstance(cell, PlotlyCell):
                    self._finalize_plotly(cell, contents_dir, sid, cid)

    def _resolve_image(self, source, to_webp, quality, save_source,
                       contents_dir, out_dir, sid, cid, i) -> str:
        import warnings
        from tessera.utils import media
        stem = f"{media.sanitize_name(sid)}__{media.sanitize_name(cid)}"
        if i:
            stem += f"__{i}"

        # matplotlib Figure (slider items) — always has bytes, no original path
        if hasattr(source, "savefig"):
            fmt = "webp" if to_webp else "svg"
            payload, mime, ext, _ = media.figure_to_payload(source, fmt, 150, quality)
            return self._place_bytes(payload, mime, ext, save_source,
                                     contents_dir, out_dir, stem)

        data, mime, ext = media.read_image_bytes(source)
        if data is None:
            # url / data: / base64 / missing — preserve previous behavior
            if self.deck.self_contained:
                from tessera.utils.image_encoder import encode
                try:
                    return encode(source)
                except FileNotFoundError:
                    return str(source)
            return str(source)

        if not to_webp and not save_source:
            # plain local image, no conversion/save → original behavior
            return media.data_uri(data, mime) if self.deck.self_contained else str(source)

        if to_webp:
            try:
                data = media.to_webp_bytes(data, quality)
                mime, ext = "image/webp", "webp"
            except RuntimeError as exc:
                warnings.warn(str(exc), stacklevel=2)   # Pillow missing → keep original
        return self._place_bytes(data, mime, ext, save_source,
                                 contents_dir, out_dir, stem)

    def _place_bytes(self, data, mime, ext, save_source,
                     contents_dir, out_dir, stem) -> str:
        """Inline (self-contained) or write-and-reference (otherwise) owned bytes."""
        from tessera.utils import media
        written = None
        need_file = save_source or (not self.deck.self_contained)
        if need_file and contents_dir is not None:
            written = media.write_asset(contents_dir, stem, ext, data)
        if self.deck.self_contained:
            return media.data_uri(data, mime)        # side file written iff save_source
        if written is not None:
            return media.rel_url(written, out_dir)
        return media.data_uri(data, mime)            # no folder (preview) → inline

    def _finalize_matplotlib(self, cell, contents_dir, out_dir, sid, cid) -> None:
        from tessera.utils import media
        if not cell.save_source or contents_dir is None:
            return   # otherwise the figure stays inline (it has no external source)
        stem = f"{media.sanitize_name(sid)}__{media.sanitize_name(cid)}"
        written = media.write_asset(contents_dir, stem, cell._ext, cell._payload)
        if not self.deck.self_contained:
            cell.resolved_src = media.rel_url(written, out_dir)

    def _finalize_plotly(self, cell, contents_dir, sid, cid) -> None:
        from tessera.utils import media
        if not cell.save_source or contents_dir is None:
            return
        stem = f"{media.sanitize_name(sid)}__{media.sanitize_name(cid)}"
        try:
            contents_dir.mkdir(parents=True, exist_ok=True)
            cell.fig.write_html(str(contents_dir / f"{stem}.html"))
        except Exception:
            pass   # never fail a write because a side artifact could not be saved

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

        # Resolve media srcs (and optionally write assets to the contents folder)
        self._finalize_media()

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
