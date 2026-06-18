"""
tessera.core.slide
===================
Defines the ``Slide`` class and slide types (SlideType).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Hashable

if TYPE_CHECKING:
    import matplotlib.figure
    import pandas as pd
    import plotly.graph_objects as go
    from tessera import Deck

from tessera.cells import (
    _UNSET,
    Cell,
    CodeCell,
    EmptyCell,
    HtmlCell,
    IframeCell,
    ImageCell,
    ImageSliderCell,
    ListCell,
    MatplotlibCell,
    MermaidCell,
    MetricCell,
    PlotlyCell,
    TableCell,
    TextCell,
    cell_method,
)

SlideType = Literal["slide", "title", "toc", "section"]


class Slide:
    """
    Represents a slide with a CSS Grid canvas of ``nrows x ncols`` cells.

    Do not instantiate directly — use the ``add_*`` methods of ``Deck``.
    """

    def __init__(
        self,
        *,
        slide_id: Hashable,
        title: str,
        subtitle: str,
        slide_type: SlideType,
        nrows: int,
        ncols: int,
        row_heights: list[int | str] | None,
        col_widths: list[int | str] | None,
        notes: str,
        cell_defaults: Any,          # CellDefaults — lazy import to avoid circular deps
        plugin_names: frozenset[str],
        parent: Deck,
        level: int = 1,
        show_toc: bool = False,
    ) -> None:
        self.slide_id     = slide_id
        self.title        = title
        self.subtitle     = subtitle
        self.slide_type   = slide_type
        self.nrows        = nrows
        self.ncols        = ncols
        self.notes        = notes
        self.level        = level
        self.show_toc     = show_toc
        self._cell_defaults = cell_defaults
        self._plugin_names  = plugin_names
        self.parent       = parent
        self._toc_entries: list[dict] = []  # populated by Assembler at write time

        # Size grid
        self.row_heights = _normalize_sizes(row_heights, nrows)
        self.col_widths  = _normalize_sizes(col_widths,  ncols)

        # Occupancy map: _occupied[row-1][col-1] = True if already allocated
        self._occupied: list[list[bool]] = [
            [False] * ncols for _ in range(nrows)
        ]

        # Cells registered in insertion order
        self._cells: list[Cell] = []
        self._cell_map: dict[Hashable, Cell] = {}
        self._next_cell_id = 1
        # Per-Jupyter-cell counters for notebook_unique cell ids (see cell_method).
        self._nb_cell_state: dict = {}

    # ------------------------------------------------------------------
    # Internals — used by @cell_method
    # ------------------------------------------------------------------

    def _resolve_position(
        self,
        col: int | None,
        row: int | None,
        colspan: int,
        rowspan: int,
    ) -> tuple[int, int]:
        """
        Resolve col/row = None to the next available canvas position.
        Scans row by row (left→right, top→bottom), skipping positions
        already occupied by other cells.
        """
        if col is not None and row is not None:
            return col, row

        # Advance cursor until a free position with enough space is found
        r, c = 1, 1
        while r <= self.nrows:
            while c <= self.ncols:
                if not self._occupied[r - 1][c - 1]:
                    # Check whether colspan/rowspan fit
                    if (
                        c + colspan - 1 <= self.ncols
                        and r + rowspan - 1 <= self.nrows
                    ):
                        return c, r
                c += 1
            c = 1
            r += 1

        from tessera.exceptions import CellPlacementError
        raise CellPlacementError(
            "No available position on the canvas to insert the cell. "
            f"Canvas {self.nrows}x{self.ncols} is already full."
        )

    def _register_cell(
        self, cell: Cell, cell_id: Hashable, index: int | None = None
    ) -> None:
        """Mark the positions occupied by the cell on the internal map.

        ``index`` is the original list position to restore when overwriting an
        existing cell (keeps render/DOM order stable); ``None`` appends.
        """
        p = cell.params
        for r in range(p.row, p.row + p.rowspan):
            for c in range(p.col, p.col + p.colspan):
                self._occupied[r - 1][c - 1] = True

        cell._slide = self   # back-reference; used by Cell._repr_html_ previews

        if index is None:
            self._cells.append(cell)
        else:
            self._cells.insert(index, cell)
        self._cell_map[cell_id] = cell

    def remove_cell(
            self,
            cell_id:Hashable,
            _caller_is_cell_method: bool = False
        ) -> None:
        if cell_id not in self._cell_map:
            raise KeyError(f"No slide found with ID: {cell_id}")
        
        cell = self._cell_map.pop(cell_id)
        self._cells.remove(cell)

        p = cell.params
        for r in range(p.row, p.row + p.rowspan):
            for c in range(p.col, p.col + p.colspan):
                self._occupied[r - 1][c - 1] = False

        # Autosave only if not called from within a cell method, to avoid 
        # multiple saves during the same operation
        if (
            (not _caller_is_cell_method) 
            and (self.parent.autosave 
                 and self.parent.autosave_level == 'cell')
        ):
            self.parent.write(self.parent.autosave)
    # ------------------------------------------------------------------
    # add_* methods — decorated with @cell_method
    # ------------------------------------------------------------------

    @cell_method
    def add_text(
        self,
        content: str,
        *,
        markdown:      bool        = True,
        col:           int | None  = None,
        row:           int | None  = None,
        colspan:       int         = 1,
        rowspan:       int         = 1,
        caption:       str         = "",
        overflow:      bool        = _UNSET,  # type: ignore[assignment]
        copy_button:   bool        = _UNSET,  # type: ignore[assignment]
        expand_button: bool        = _UNSET,  # type: ignore[assignment]
        transparent:   bool        = _UNSET,  # type: ignore[assignment]
        halign:        str         = _UNSET,  # type: ignore[assignment]
        valign:        str         = _UNSET,  # type: ignore[assignment]
        _params: Any               = None,    # injected by the decorator
    ) -> TextCell:
        return TextCell(content=content, params=_params, markdown=markdown)

    @cell_method
    def add_image(
        self,
        source: "str | Any",       # str | Path | matplotlib Figure
        *,
        lightbox:      bool        = True,
        to_webp:       bool        = False,
        webp_quality:  int | None  = None,
        save_source:   bool        = False,
        col:           int | None  = None,
        row:           int | None  = None,
        colspan:       int         = 1,
        rowspan:       int         = 1,
        caption:       str         = "",
        overflow:      bool        = _UNSET,  # type: ignore[assignment]
        copy_button:   bool        = _UNSET,  # type: ignore[assignment]
        expand_button: bool        = _UNSET,  # type: ignore[assignment]
        _params: Any               = None,
    ) -> "ImageCell | MatplotlibCell":
        # A matplotlib Figure routes through the matplotlib pipeline (coherent
        # with add_image_slider). Duck-typed so matplotlib stays an optional dep.
        if hasattr(source, "savefig"):
            return MatplotlibCell(
                fig=source, dpi=150,
                fmt="webp" if to_webp else "svg",
                lightbox=lightbox, params=_params,
                webp_quality=webp_quality, save_source=save_source,
            )
        return ImageCell(
            source=source, lightbox=lightbox, params=_params,
            to_webp=to_webp, webp_quality=webp_quality, save_source=save_source,
        )

    @cell_method
    def add_table(
        self,
        data: "dict[str, Any] | list[list[Any]] | pd.DataFrame | str",
        *,
        separator:     Literal["auto", ",", "\t"] = "auto",
        index:         bool        = False,
        col:           int | None  = None,
        row:           int | None  = None,
        colspan:       int         = 1,
        rowspan:       int         = 1,
        caption:       str         = "",
        overflow:      bool        = _UNSET,  # type: ignore[assignment]
        copy_button:   bool        = _UNSET,  # type: ignore[assignment]
        expand_button: bool        = _UNSET,  # type: ignore[assignment]
        _params: Any               = None,
    ) -> TableCell:
        return TableCell(data=data, separator=separator, index=index, params=_params)

    @cell_method
    def add_list(
        self,
        items: list[Any],
        *,
        ordered:       bool        = False,
        col:           int | None  = None,
        row:           int | None  = None,
        colspan:       int         = 1,
        rowspan:       int         = 1,
        caption:       str         = "",
        overflow:      bool        = _UNSET,  # type: ignore[assignment]
        copy_button:   bool        = _UNSET,  # type: ignore[assignment]
        expand_button: bool        = _UNSET,  # type: ignore[assignment]
        _params: Any               = None,
    ) -> ListCell:
        return ListCell(items=items, ordered=ordered, params=_params)

    @cell_method
    def add_plotly(
        self,
        fig: "go.Figure",
        *,
        save_source:   bool        = False,
        col:           int | None  = None,
        row:           int | None  = None,
        colspan:       int         = 1,
        rowspan:       int         = 1,
        caption:       str         = "",
        overflow:      bool        = _UNSET,  # type: ignore[assignment]
        copy_button:   bool        = _UNSET,  # type: ignore[assignment]
        expand_button: bool        = _UNSET,  # type: ignore[assignment]
        _params: Any               = None,
    ) -> PlotlyCell:
        self._require_plugin("plotly", "add_plotly")
        return PlotlyCell(fig=fig, params=_params, save_source=save_source)

    @cell_method
    def add_matplotlib(
        self,
        fig: "matplotlib.figure.Figure",
        *,
        dpi:           int         = 150,
        fmt:           str         = "svg",
        to_webp:       bool        = False,
        webp_quality:  int | None  = None,
        save_source:   bool        = False,
        lightbox:      bool        = True,
        col:           int | None  = None,
        row:           int | None  = None,
        colspan:       int         = 1,
        rowspan:       int         = 1,
        caption:       str         = "",
        overflow:      bool        = _UNSET,  # type: ignore[assignment]
        copy_button:   bool        = _UNSET,  # type: ignore[assignment]
        expand_button: bool        = _UNSET,  # type: ignore[assignment]
        transparent:   bool        = _UNSET,  # type: ignore[assignment]
        halign:        str         = _UNSET,  # type: ignore[assignment]
        valign:        str         = _UNSET,  # type: ignore[assignment]
        _params: Any               = None,
    ) -> MatplotlibCell:
        if to_webp:
            fmt = "webp"
        return MatplotlibCell(
            fig=fig, dpi=dpi, fmt=fmt, lightbox=lightbox, params=_params,
            webp_quality=webp_quality, save_source=save_source,
        )

    @cell_method
    def add_code(
        self,
        code: str,
        *,
        language:      str         = "python",
        col:           int | None  = None,
        row:           int | None  = None,
        colspan:       int         = 1,
        rowspan:       int         = 1,
        caption:       str         = "",
        overflow:      bool        = _UNSET,  # type: ignore[assignment]
        copy_button:   bool        = _UNSET,  # type: ignore[assignment]
        expand_button: bool        = _UNSET,  # type: ignore[assignment]
        _params: Any               = None,
    ) -> CodeCell:
        self._require_plugin("highlight", "add_code")
        return CodeCell(code=code, language=language, params=_params)

    @cell_method
    def add_metric(
        self,
        value: "int | float | str",
        label: str,
        *,
        delta:           "int | float | str | None" = None,
        delta_label:     str         = "",
        lower_is_better: bool        = False,
        symbol_good:     str         = "▲",
        symbol_bad:      str         = "▼",
        symbol_neutral:  str         = "—",
        color_good:      str         = "#4ade80",
        color_bad:       str         = "#f87171",
        color_neutral:   str         = "",
        col:             int | None  = None,
        row:             int | None  = None,
        colspan:         int         = 1,
        rowspan:         int         = 1,
        caption:         str         = "",
        overflow:        bool        = _UNSET,  # type: ignore[assignment]
        copy_button:     bool        = _UNSET,  # type: ignore[assignment]
        expand_button:   bool        = _UNSET,  # type: ignore[assignment]
        _params: Any                 = None,
    ) -> MetricCell:
        return MetricCell(
            value=value, label=label,
            delta=delta, delta_label=delta_label,
            lower_is_better=lower_is_better,
            symbol_good=symbol_good,
            symbol_bad=symbol_bad,
            symbol_neutral=symbol_neutral,
            color_good=color_good,
            color_bad=color_bad,
            color_neutral=color_neutral,
            params=_params,
        )

    @cell_method
    def add_mermaid(
        self,
        diagram: str,
        *,
        col:           int | None  = None,
        row:           int | None  = None,
        colspan:       int         = 1,
        rowspan:       int         = 1,
        caption:       str         = "",
        overflow:      bool        = _UNSET,  # type: ignore[assignment]
        copy_button:   bool        = _UNSET,  # type: ignore[assignment]
        expand_button: bool        = _UNSET,  # type: ignore[assignment]
        _params: Any               = None,
    ) -> MermaidCell:
        self._require_plugin("mermaid", "add_mermaid")
        return MermaidCell(diagram=diagram, params=_params)

    @cell_method
    def add_html(
        self,
        content: str,
        *,
        col:           int | None  = None,
        row:           int | None  = None,
        colspan:       int         = 1,
        rowspan:       int         = 1,
        caption:       str         = "",
        overflow:      bool        = _UNSET,  # type: ignore[assignment]
        copy_button:   bool        = _UNSET,  # type: ignore[assignment]
        expand_button: bool        = _UNSET,  # type: ignore[assignment]
        _params: Any               = None,
    ) -> HtmlCell:
        return HtmlCell(content=content, params=_params)

    @cell_method
    def add_iframe(
        self,
        url: str,
        *,
        col:           int | None  = None,
        row:           int | None  = None,
        colspan:       int         = 1,
        rowspan:       int         = 1,
        caption:       str         = "",
        overflow:      bool        = _UNSET,  # type: ignore[assignment]
        copy_button:   bool        = _UNSET,  # type: ignore[assignment]
        expand_button: bool        = _UNSET,  # type: ignore[assignment]
        _params: Any               = None,
    ) -> IframeCell:
        return IframeCell(url=url, params=_params)

    @cell_method
    def add_empty(
        self,
        *,
        col:     int | None = None,
        row:     int | None = None,
        colspan: int        = 1,
        rowspan: int        = 1,
        transparent: bool   = _UNSET,  # type: ignore[assignment]
        halign:      str    = _UNSET,  # type: ignore[assignment]
        valign:      str    = _UNSET,  # type: ignore[assignment]
        _params: Any        = None,
    ) -> EmptyCell:
        return EmptyCell(params=_params)

    @cell_method
    def add_image_slider(
        self,
        sources: "list",
        *,
        captions:      "list | None" = None,
        to_webp:       bool        = False,
        webp_quality:  int | None  = None,
        save_source:   bool        = False,
        col:           int | None  = None,
        row:           int | None  = None,
        colspan:       int         = 1,
        rowspan:       int         = 1,
        caption:       str         = "",
        overflow:      bool        = _UNSET,  # type: ignore[assignment]
        copy_button:   bool        = _UNSET,  # type: ignore[assignment]
        expand_button: bool        = _UNSET,  # type: ignore[assignment]
        _params: Any               = None,
    ) -> "ImageSliderCell":
        from pathlib import Path
        import re
        resolved = []
        for s in sources:
            if hasattr(s, "savefig"):       # matplotlib Figure — keep, encode at write
                resolved.append(s)
                continue
            sv = str(s)
            if not sv.startswith(("http://", "https://", "data:")) and not (len(sv) > 64 and bool(re.fullmatch(r"[A-Za-z0-9+/=\n]+", sv))):
                resolved.append(Path(sv).resolve())
            else:
                resolved.append(sv)
        img_captions = captions or [""] * len(sources)
        return ImageSliderCell(
            sources=resolved, captions=img_captions, params=_params,
            to_webp=to_webp, webp_quality=webp_quality, save_source=save_source,
        )

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------

    def _require_plugin(self, plugin_name: str, method_name: str) -> None:
        from tessera.exceptions import PluginNotDeclaredError
        if plugin_name not in self._plugin_names:
            raise PluginNotDeclaredError(
                f"{method_name}() requires Plugin('{plugin_name}'), "
                f"but it was not declared in Deck(plugins=[…])"
            )

    def __repr__(self) -> str:
        return (
            f"Slide(id={self.slide_id!r}, type={self.slide_type!r}, "
            f"title={self.title!r}, grid={self.nrows}x{self.ncols})"
        )

    def _repr_html_(self) -> str:
        """Render an inline, chrome-free preview of this slide for Jupyter."""
        from tessera.core.assembler import Assembler
        from tessera.utils.notebook import (
            SLIDE_PREVIEW_HEIGHT, iframe_srcdoc, preview_error,
        )
        try:
            deck = self.parent._preview_clone([self], sections=self.parent._sections)
            html = Assembler(deck)._render()
            return iframe_srcdoc(html, height=self.parent.preview_height or SLIDE_PREVIEW_HEIGHT)
        except Exception as exc:   # never break the notebook on a preview failure
            return preview_error(self, exc)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def cells(self):
        return list(self._cells)
    
    @property 
    def cell_map(self):
        return dict(self._cell_map)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_sizes(
    sizes: list[int | str] | None,
    count: int,
) -> list[str]:
    """
    Normalise row_heights / col_widths to a list of CSS strings with
    exactly ``count`` entries.

    - int  → "<n>px"
    - str  → kept as-is ("30%", "1fr", "200px", …)
    - None or list shorter than count → padded with "1fr"
    """
    result: list[str] = []
    if sizes:
        for s in sizes[:count]:
            result.append(f"{s}px" if isinstance(s, int) else s)
    # Pad missing entries with "1fr"
    while len(result) < count:
        result.append("1fr")
    return result
