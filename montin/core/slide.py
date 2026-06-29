"""
montin.core.slide
===================
Defines the ``Slide`` class and slide types (SlideType).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Hashable

if TYPE_CHECKING:
    import matplotlib.figure
    import pandas as pd
    import plotly.graph_objects as go
    from montin import Deck

from montin.cells import (
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
    TabulatorCell,
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

        from montin.exceptions import CellPlacementError
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
        """Remove a cell from the slide and free its grid positions.

        Args:
            cell_id: The identifier of the cell to remove, as returned by
                the cell's ``cell_id`` attribute or used as a key in
                ``cell_map``.

        Raises:
            KeyError: If no cell with ``cell_id`` exists on this slide.
        """
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
        fontscale:     float       = _UNSET,  # type: ignore[assignment]
        _params: Any               = None,    # injected by the decorator
    ) -> TextCell:
        """Add a text cell to the slide.

        Content is rendered as Markdown by default. Supports standard Markdown
        (headings, bold, italic, lists, code spans, links) and LaTeX math
        (``$...$`` / ``$$...$$``) when ``Plugins.MathJax()`` is declared on
        the deck.

        Args:
            content: Text to display. Parsed as Markdown unless
                ``markdown=False``.
            markdown: If ``True`` (default), render ``content`` as Markdown.
                Pass ``False`` to display plain text without parsing.
            col: Grid column (1-based). Auto-placed when omitted.
            row: Grid row (1-based). Auto-placed when omitted.
            colspan: Number of grid columns to span (default ``1``).
            rowspan: Number of grid rows to span (default ``1``).
            caption: Caption text displayed below the cell.
            overflow: Show a scrollbar instead of clipping content.
            copy_button: Show a copy-to-clipboard button on the cell card.
            expand_button: Show a fullscreen-expand button on the cell card.
            transparent: If ``True``, the cell background is transparent.
            halign: Horizontal alignment — ``"left"``, ``"center"``,
                or ``"right"``.
            valign: Vertical alignment — ``"top"``, ``"middle"``,
                or ``"bottom"``.
            fontscale: Multiplier for this cell's text size (default ``1.0``).
                Composes on top of the deck-wide ``fontsize_scale``.

        Returns:
            TextCell: The newly created and registered text cell.
        """
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
        """Add an image to the slide.

        Accepts a file path, URL, base64 data URI, or a matplotlib ``Figure``.
        Matplotlib figures are rendered to SVG (default) or WebP and embedded
        inline. Clicking the image opens a lightbox viewer by default.

        Args:
            source: Image source. One of:

                - File path (``str`` or ``pathlib.Path``) to a PNG/JPG/SVG/WebP.
                - URL (``"https://..."``).
                - Base64 data URI.
                - ``matplotlib.figure.Figure`` — rendered to SVG or WebP and
                  embedded inline.

            lightbox: If ``True`` (default), clicking the image opens it in a
                fullscreen lightbox viewer.
            to_webp: Convert to WebP before embedding. Reduces file size for
                photographs; for matplotlib figures uses WebP instead of SVG.
            webp_quality: WebP quality level (1–100). ``None`` uses the
                encoder's default (~80).
            save_source: If ``True``, embed the original source file alongside
                the processed image so it can be recovered from the HTML.
            col: Grid column (1-based). Auto-placed when omitted.
            row: Grid row (1-based). Auto-placed when omitted.
            colspan: Number of grid columns to span (default ``1``).
            rowspan: Number of grid rows to span (default ``1``).
            caption: Caption text displayed below the image.
            overflow: Show a scrollbar on the cell instead of clipping.
            copy_button: Show a copy-to-clipboard button on the cell card.
            expand_button: Show a fullscreen-expand button on the cell card.

        Returns:
            ImageCell | MatplotlibCell: ``MatplotlibCell`` when ``source`` is a
            matplotlib ``Figure``, otherwise ``ImageCell``.
        """
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
        """Add a static HTML table to the slide.

        Renders a plain, non-interactive ``<table>``. For sortable, filterable,
        and paginated tables use ``add_tabulator`` instead.

        Args:
            data: Tabular data. Accepts:

                - ``dict[str, list]`` — keys = column headers, values = columns.
                - ``list[list]`` — first sub-list is the header row.
                - ``pandas.DataFrame``.
                - A CSV/TSV string.
                - A path to a CSV/TSV file.

            separator: Field separator for string or file inputs. ``"auto"``
                (default) detects a tab in the first line; otherwise ``","``
                or ``"\\t"``.
            index: For pandas DataFrames only — if ``True``, include the index
                as the first column.
            col: Grid column (1-based). Auto-placed when omitted.
            row: Grid row (1-based). Auto-placed when omitted.
            colspan: Number of grid columns to span (default ``1``).
            rowspan: Number of grid rows to span (default ``1``).
            caption: Caption text displayed below the table.
            overflow: Show a scrollbar when the table overflows the cell.
            copy_button: Show a copy-to-clipboard button on the cell card.
            expand_button: Show a fullscreen-expand button on the cell card.

        Returns:
            TableCell: The newly created and registered table cell.
        """
        return TableCell(data=data, separator=separator, index=index, params=_params)

    @cell_method
    def add_tabulator(
        self,
        data: "dict[str, Any] | list[list[Any]] | pd.DataFrame | str | None" = None,
        *,
        sheets:          "dict[str, Any] | None"    = None,
        columns:         list[dict] | None          = None,
        options:         dict | None                = None,
        layout:          str                        = "fitColumns",
        responsive:      bool                       = False,
        pagination:      int | None                 = None,
        selectable:      bool | int                 = False,
        group_by:        str | list[str] | None     = None,
        header_filter:   bool                       = False,
        frozen_columns:  list[str] | None           = None,
        frozen_rows:     int | None                 = None,
        movable_columns: bool                       = True,
        header_sort:     bool | None                = None,
        row_numbers:     bool                       = False,
        spreadsheet_mode: bool                      = False,
        persistence:     bool                       = False,
        download:        list[str] | None           = None,
        height:          str | int | None           = None,
        index:           bool                       = False,
        separator:       Literal["auto", ",", "\t"] = "auto",
        col:             int | None                 = None,
        row:             int | None                 = None,
        colspan:         int                        = 1,
        rowspan:         int                        = 1,
        caption:         str                        = "",
        overflow:        bool                       = False,
        copy_button:     bool                       = _UNSET,  # type: ignore[assignment]
        expand_button:   bool                       = _UNSET,  # type: ignore[assignment]
        tabulator_config: dict | None               = None,
        _params: Any                                = None,
    ) -> TabulatorCell:
        """Add an interactive Tabulator.js table to the slide.

        Requires ``Plugins.Tabulator()`` in the deck's plugin list. The table
        supports sorting, filtering, pagination, grouping, row/column selection,
        spreadsheet-style editing, clipboard copy/paste, and CSV/JSON export —
        all self-contained inside the HTML file with no external requests when
        using the default bundled source.

        Pass ``data`` for a single interactive table, or ``sheets`` for a
        multi-tab view (like an Excel workbook). Both accept the same input
        types as ``add_table``: a ``dict`` of columns, a ``list[list]``
        (first row = headers), a pandas ``DataFrame``, a CSV/TSV string, or a
        path to a CSV/TSV file.

        Args:
            data: Tabular data for a single-sheet table. Accepts
                ``dict[str, list]`` (keys = column headers), ``list[list]``
                (first row = headers), a pandas ``DataFrame``, a CSV/TSV
                string, or a CSV/TSV file path. Defaults to ``None``;
                mutually exclusive with ``sheets``.
            sheets: Multi-sheet mode. A ``dict`` whose keys become tab titles
                and whose values are each parsed as tabular data (same types as
                ``data``). Column headers appear as the first row of each
                sheet's grid. Mutually exclusive with ``data``. Sorting,
                filtering, pagination, and grouping options are ignored in
                multi-sheet mode.
            columns: Per-column Tabulator column definitions merged over the
                auto-generated columns. Each dict is matched by ``"title"``
                (or ``"field"``) — only changed keys need to be specified.
                Useful keys: ``"formatter"`` (``"money"``, ``"star"``,
                ``"progress"``, ``"tickCross"``), ``"editor"``,
                ``"bottomCalc"`` / ``"topCalc"``, ``"frozen"``,
                ``"headerFilter"``, ``"widthGrow"``.
            options: Verbatim dict merged into the Tabulator constructor,
                overriding all named keyword options. Use for anything not
                exposed by name — ``"movableRows"``, ``"history"``,
                ``"locale"``, nested tables, etc.
            layout: Column sizing strategy. One of ``"fitColumns"`` (default),
                ``"fitData"``, ``"fitDataFill"``, ``"fitDataStretch"``, or
                ``"fitDataTable"``.
            responsive: Collapse overflowing columns into an expandable row
                instead of horizontal scroll. Defaults to ``False``.
            pagination: Page size (rows per page). ``None`` renders all rows.
            selectable: ``True`` or a max-count integer to allow row selection.
            group_by: Column title (or list of titles) to group rows under
                collapsible section headers.
            header_filter: Add a text filter input to every column header.
            frozen_columns: Column titles to pin to the left edge.
            frozen_rows: Number of rows to pin to the top.
            movable_columns: Allow readers to drag column headers to reorder
                them. Defaults to ``True``.
            header_sort: ``True`` / ``False`` to force column-header sorting
                on or off. ``None`` keeps Tabulator's default (sortable).
                Defaults to ``False`` in ``spreadsheet_mode``.
            row_numbers: Add a frozen left column with sequential row numbers.
                Numbers are continuous across paginated pages.
            spreadsheet_mode: Enable range cell selection and clipboard
                copy/paste (Ctrl-C / Ctrl-V). In ``sheets`` mode also makes
                cells editable.
            persistence: Save the reader's sort / filter / column-order tweaks
                in ``localStorage`` and restore on reload. Off by default; the
                persistence key includes a column-structure hash so stale state
                is discarded automatically when the table changes.
            download: Export buttons to show on the cell. Accepts ``["csv"]``,
                ``["json"]``, or both. xlsx is not supported (needs SheetJS).
                In multi-sheet mode downloads the active sheet only.
            height: Fixed height for the table, e.g. ``"400px"`` or ``400``
                (px). Enables Tabulator's virtual rendering for large tables.
            index: Include the pandas DataFrame index as the first column.
            separator: ``"auto"`` (detect from first line), ``","`` or
                ``"\\t"`` — for string or file inputs only.
            col: Grid column (1-based). Auto-placed when omitted.
            row: Grid row (1-based). Auto-placed when omitted.
            colspan: Number of grid columns to span (default ``1``).
            rowspan: Number of grid rows to span (default ``1``).
            caption: Caption text displayed below the table.
            overflow: Show a scrollbar on the cell instead of clipping.
                Defaults to ``False`` (Tabulator scrolls internally).
            copy_button: Show a copy-to-clipboard button on the cell card.
            expand_button: Show a fullscreen-expand button on the cell card.
            tabulator_config: Final-pass dict merged after all other options,
                overriding even ``options``.

        Returns:
            TabulatorCell: The newly created and registered table cell.

        Raises:
            PluginNotDeclaredError: If ``Plugins.Tabulator()`` is not in the
                deck's plugin list.
            ValueError: If both ``data`` and ``sheets`` are supplied, or if
                neither is supplied.
        """
        self._require_plugin("tabulator", "add_tabulator")
        return TabulatorCell(
            data=data, params=_params,
            sheets=sheets,
            columns=columns, options=options, layout=layout,
            responsive=responsive, pagination=pagination, selectable=selectable,
            group_by=group_by, header_filter=header_filter,
            frozen_columns=frozen_columns, frozen_rows=frozen_rows,
            movable_columns=movable_columns, header_sort=header_sort,
            row_numbers=row_numbers, spreadsheet_mode=spreadsheet_mode,
            persistence=persistence,
            download=download, height=height, index=index, separator=separator,
            tabulator_config=tabulator_config,
        )

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
        """Add a bulleted or numbered list to the slide.

        Args:
            items: The list items to display. Each element is converted to a
                string and rendered as a list entry.
            ordered: If ``True``, render as a numbered (``<ol>``) list.
                Defaults to ``False`` (bulleted ``<ul>``).
            col: Grid column (1-based). Auto-placed when omitted.
            row: Grid row (1-based). Auto-placed when omitted.
            colspan: Number of grid columns to span (default ``1``).
            rowspan: Number of grid rows to span (default ``1``).
            caption: Caption text displayed below the list.
            overflow: Show a scrollbar on the cell instead of clipping.
            copy_button: Show a copy-to-clipboard button on the cell card.
            expand_button: Show a fullscreen-expand button on the cell card.

        Returns:
            ListCell: The newly created and registered list cell.
        """
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
        """Add an interactive Plotly chart to the slide.

        Requires ``Plugins.Plotly()`` in the deck's plugin list. The full
        Plotly figure JSON is embedded in the HTML; the chart is interactive
        (zoom, pan, hover tooltips) without any server round-trips.

        Args:
            fig: A ``plotly.graph_objects.Figure`` instance.
            save_source: If ``True``, embed the raw figure JSON alongside the
                rendered chart so it can be recovered from the HTML.
            col: Grid column (1-based). Auto-placed when omitted.
            row: Grid row (1-based). Auto-placed when omitted.
            colspan: Number of grid columns to span (default ``1``).
            rowspan: Number of grid rows to span (default ``1``).
            caption: Caption text displayed below the chart.
            overflow: Show a scrollbar on the cell instead of clipping.
            copy_button: Show a copy-to-clipboard button on the cell card.
            expand_button: Show a fullscreen-expand button on the cell card.

        Returns:
            PlotlyCell: The newly created and registered Plotly chart cell.

        Raises:
            PluginNotDeclaredError: If ``Plugins.Plotly()`` is not in the
                deck's plugin list.
        """
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
        fontscale:     float       = _UNSET,  # type: ignore[assignment]
        _params: Any               = None,
    ) -> MatplotlibCell:
        """Add a matplotlib figure to the slide.

        The figure is rendered to SVG (vector, lossless) or WebP (raster) and
        embedded as a base64 data URI — no external files needed. For
        interactive charts see ``add_plotly``.

        Args:
            fig: A ``matplotlib.figure.Figure`` instance.
            dpi: Render resolution in dots per inch. Only meaningful when
                ``fmt="webp"`` (SVG is resolution-independent). Defaults to
                ``150``.
            fmt: Output format — ``"svg"`` (default, vector) or ``"webp"``
                (raster). Overridden to ``"webp"`` when ``to_webp=True``.
            to_webp: If ``True``, forces WebP output regardless of ``fmt``.
            webp_quality: WebP quality level (1–100). ``None`` uses the
                encoder's default.
            save_source: If ``True``, the figure is pickled and embedded
                alongside the rendered image so it can be recovered later.
            lightbox: If ``True`` (default), clicking the figure opens it in
                a fullscreen lightbox viewer.
            col: Grid column (1-based). Auto-placed when omitted.
            row: Grid row (1-based). Auto-placed when omitted.
            colspan: Number of grid columns to span (default ``1``).
            rowspan: Number of grid rows to span (default ``1``).
            caption: Caption text displayed below the figure.
            overflow: Show a scrollbar on the cell instead of clipping.
            copy_button: Show a copy-to-clipboard button on the cell card.
            expand_button: Show a fullscreen-expand button on the cell card.
            transparent: If ``True``, the cell background is transparent.
            halign: Horizontal alignment — ``"left"``, ``"center"``,
                or ``"right"``.
            valign: Vertical alignment — ``"top"``, ``"middle"``,
                or ``"bottom"``.
            fontscale: Multiplier for this cell's text size (default ``1.0``).
                Composes on top of the deck-wide ``fontsize_scale``.

        Returns:
            MatplotlibCell: The newly created and registered figure cell.
        """
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
        """Add a syntax-highlighted code block to the slide.

        Requires ``Plugins.Highlight()`` in the deck's plugin list. Highlighting
        is applied by Highlight.js at render time in the browser.

        Args:
            code: The source code string to display.
            language: Language identifier for syntax highlighting, e.g.
                ``"python"``, ``"javascript"``, ``"sql"``, ``"bash"``.
                Passed directly to Highlight.js. Defaults to ``"python"``.
            col: Grid column (1-based). Auto-placed when omitted.
            row: Grid row (1-based). Auto-placed when omitted.
            colspan: Number of grid columns to span (default ``1``).
            rowspan: Number of grid rows to span (default ``1``).
            caption: Caption text displayed below the code block.
            overflow: Show a scrollbar instead of wrapping long lines.
            copy_button: Show a copy-to-clipboard button on the cell card.
            expand_button: Show a fullscreen-expand button on the cell card.

        Returns:
            CodeCell: The newly created and registered code cell.

        Raises:
            PluginNotDeclaredError: If ``Plugins.Highlight()`` is not in the
                deck's plugin list.
        """
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
        """Add a KPI metric card to the slide.

        Displays a prominent value with a label and an optional delta indicator
        (change vs a reference value), colour-coded green / red / neutral.

        Args:
            value: The primary metric value. Accepts ``int``, ``float``, or a
                pre-formatted ``str`` (e.g. ``"€ 1,234"``).
            label: Short descriptor shown below the value (e.g.
                ``"Revenue"``).
            delta: Change from a reference value shown as a secondary line with
                a directional symbol. ``None`` hides the delta row entirely.
            delta_label: Optional text appended after the delta value (e.g.
                ``"vs last year"``).
            lower_is_better: If ``True``, a negative delta is coloured green
                and a positive delta red — useful for metrics like error rate
                or cost. Defaults to ``False``.
            symbol_good: Symbol prepended to a favourable delta. Defaults to
                ``"▲"``.
            symbol_bad: Symbol prepended to an unfavourable delta. Defaults to
                ``"▼"``.
            symbol_neutral: Symbol shown when delta is exactly zero. Defaults
                to ``"—"``.
            color_good: CSS colour for a favourable delta. Defaults to
                ``"#4ade80"`` (green).
            color_bad: CSS colour for an unfavourable delta. Defaults to
                ``"#f87171"`` (red).
            color_neutral: CSS colour for a neutral delta. Defaults to ``""``
                (inherits the theme text colour).
            col: Grid column (1-based). Auto-placed when omitted.
            row: Grid row (1-based). Auto-placed when omitted.
            colspan: Number of grid columns to span (default ``1``).
            rowspan: Number of grid rows to span (default ``1``).
            caption: Caption text displayed below the metric card.
            overflow: Show a scrollbar on the cell instead of clipping.
            copy_button: Show a copy-to-clipboard button on the cell card.
            expand_button: Show a fullscreen-expand button on the cell card.

        Returns:
            MetricCell: The newly created and registered metric cell.
        """
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
        """Add a Mermaid diagram to the slide.

        Requires ``Plugins.Mermaid()`` in the deck's plugin list. The diagram
        string is rendered to SVG client-side by Mermaid.js on first display.
        Supported types include flowcharts, sequence diagrams, Gantt charts,
        class diagrams, ER diagrams, pie charts, and more.

        Args:
            diagram: A Mermaid diagram definition string, e.g.::

                \"\"\"
                flowchart LR
                    A --> B --> C
                \"\"\"

            col: Grid column (1-based). Auto-placed when omitted.
            row: Grid row (1-based). Auto-placed when omitted.
            colspan: Number of grid columns to span (default ``1``).
            rowspan: Number of grid rows to span (default ``1``).
            caption: Caption text displayed below the diagram.
            overflow: Show a scrollbar on the cell instead of clipping.
            copy_button: Show a copy-to-clipboard button on the cell card.
            expand_button: Show a fullscreen-expand button on the cell card.

        Returns:
            MermaidCell: The newly created and registered diagram cell.

        Raises:
            PluginNotDeclaredError: If ``Plugins.Mermaid()`` is not in the
                deck's plugin list.
        """
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
        """Add a raw HTML cell to the slide.

        The content is injected verbatim into the slide DOM without escaping
        or sanitisation. Use for custom widgets, embedded SVGs, or any markup
        that Montin's other cells do not cover.

        Args:
            content: Raw HTML string to inject into the cell body.
            col: Grid column (1-based). Auto-placed when omitted.
            row: Grid row (1-based). Auto-placed when omitted.
            colspan: Number of grid columns to span (default ``1``).
            rowspan: Number of grid rows to span (default ``1``).
            caption: Caption text displayed below the HTML block.
            overflow: Show a scrollbar on the cell instead of clipping.
            copy_button: Show a copy-to-clipboard button on the cell card.
            expand_button: Show a fullscreen-expand button on the cell card.

        Returns:
            HtmlCell: The newly created and registered HTML cell.
        """
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
        """Embed an external URL in an iframe cell.

        The URL is loaded in a sandboxed ``<iframe>`` at render time. The
        report must be opened in a browser with network access for the embedded
        page to load.

        Args:
            url: The URL to embed (e.g. ``"https://example.com"``).
            col: Grid column (1-based). Auto-placed when omitted.
            row: Grid row (1-based). Auto-placed when omitted.
            colspan: Number of grid columns to span (default ``1``).
            rowspan: Number of grid rows to span (default ``1``).
            caption: Caption text displayed below the iframe.
            overflow: Show a scrollbar on the cell instead of clipping.
            copy_button: Show a copy-to-clipboard button on the cell card.
            expand_button: Show a fullscreen-expand button on the cell card.

        Returns:
            IframeCell: The newly created and registered iframe cell.
        """
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
        fontscale:   float  = _UNSET,  # type: ignore[assignment]
        _params: Any        = None,
    ) -> EmptyCell:
        """Add an empty placeholder cell to reserve space on the grid.

        Useful for leaving intentional gaps in complex layouts — for example,
        to place content in columns 1 and 3 while keeping column 2 blank.

        Args:
            col: Grid column (1-based). Auto-placed when omitted.
            row: Grid row (1-based). Auto-placed when omitted.
            colspan: Number of grid columns to span (default ``1``).
            rowspan: Number of grid rows to span (default ``1``).
            transparent: If ``True``, the placeholder has no background and no
                border — invisible to the reader.
            halign: Horizontal alignment — ``"left"``, ``"center"``,
                or ``"right"``.
            valign: Vertical alignment — ``"top"``, ``"middle"``,
                or ``"bottom"``.
            fontscale: Multiplier for this cell's text size (default ``1.0``).
                Composes on top of the deck-wide ``fontsize_scale``.

        Returns:
            EmptyCell: The newly created and registered empty cell.
        """
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
        """Add an image carousel to the slide.

        Displays a sequence of images (or matplotlib figures) as a navigable
        slideshow with previous/next controls. Each image can have its own
        overlay caption.

        Args:
            sources: Ordered list of image sources. Each element may be:

                - A file path (``str`` or ``pathlib.Path``).
                - A URL (``"https://..."``).
                - A base64 data URI.
                - A ``matplotlib.figure.Figure`` — rendered inline.

            captions: Per-image caption strings displayed as overlays. Must
                match the length of ``sources`` when provided. Defaults to
                empty strings for all images.
            to_webp: Convert raster images to WebP before embedding. Reduces
                file size for photographs.
            webp_quality: WebP quality level (1–100). ``None`` uses the
                encoder's default.
            save_source: If ``True``, original source files are embedded
                alongside the processed images.
            col: Grid column (1-based). Auto-placed when omitted.
            row: Grid row (1-based). Auto-placed when omitted.
            colspan: Number of grid columns to span (default ``1``).
            rowspan: Number of grid rows to span (default ``1``).
            caption: Master caption displayed below the entire slider cell.
            overflow: Show a scrollbar on the cell instead of clipping.
            copy_button: Show a copy-to-clipboard button on the cell card.
            expand_button: Show a fullscreen-expand button on the cell card.

        Returns:
            ImageSliderCell: The newly created and registered slider cell.
        """
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
        from montin.exceptions import PluginNotDeclaredError
        if plugin_name not in self._plugin_names:
            hint = {
                "plotly":    "Plugins.Plotly()",
                "mermaid":   "Plugins.Mermaid()",
                "highlight": "Plugins.Highlight()",
                "mathjax":   "Plugins.MathJax()",
                "tabulator": "Plugins.Tabulator()",
            }.get(plugin_name, f"the '{plugin_name}' plugin")
            raise PluginNotDeclaredError(
                f"{method_name}() requires {hint}; declare it in "
                f"Deck(plugins=[...])."
            )

    def __repr__(self) -> str:
        return (
            f"Slide(id={self.slide_id!r}, type={self.slide_type!r}, "
            f"title={self.title!r}, grid={self.nrows}x{self.ncols})"
        )

    def _repr_html_(self) -> str:
        """Render an inline, chrome-free preview of this slide for Jupyter."""
        from montin.core.assembler import Assembler
        from montin.utils.notebook import (
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
    def cells(self) -> "list[Cell]":
        """Ordered list of all cells registered on this slide."""
        return list(self._cells)

    @property
    def cell_map(self) -> "dict[Hashable, Cell]":
        """Mapping from cell id to cell object for all cells on this slide."""
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
