"""
tessera.core.slides
====================
Defines ``HTMLSlides``, ``Plugin``, ``SlideDefaults``, and ``CellDefaults``.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Hashable, Literal

from tessera.cells import _UNSET
from tessera.core.slide import Slide


# ---------------------------------------------------------------------------
# Plugin
# ---------------------------------------------------------------------------

@dataclass
class Plugin:
    """Declares an optional JS library and its loading mode."""

    name:   Literal["mathjax", "plotly", "highlight", "mermaid"]
    source: Literal["bundled", "cdn"] = "bundled"


# ---------------------------------------------------------------------------
# Configurable defaults
# ---------------------------------------------------------------------------

@dataclass
class SlideDefaults:
    """Grid layout defaults applied to every :meth:`~HTMLSlides.add_slide` call.

    Any value set here acts as the fallback when the corresponding argument is
    omitted from ``add_slide()``. Per-call arguments always take precedence.

    Attributes:
        nrows: Number of grid rows (default ``1``).
        ncols: Number of grid columns (default ``1``).
        row_heights: CSS height for each row (e.g. ``["2fr", "1fr"]``).
            ``None`` distributes space evenly.
        col_widths: CSS width for each column (e.g. ``["300px", "1fr"]``).
            ``None`` distributes space evenly.
    """

    nrows:       int                      = 1
    ncols:       int                      = 1
    row_heights: list[int | str] | None   = None
    col_widths:  list[int | str] | None   = None


@dataclass
class CellDefaults:
    """Visual and behaviour defaults applied to every ``add_*()`` cell method.

    Any value set here acts as the fallback when the corresponding argument is
    omitted from a cell-creation call. Per-call arguments always take precedence.

    Attributes:
        overflow: Whether cell content is scrollable when it overflows
            (default ``True``).
        copy_button: Show a copy-to-clipboard button on the cell
            (default ``False``).
        expand_button: Show a fullscreen-expand button on the cell
            (default ``False``).
        transparent: Render the cell without a background card
            (default ``False``).
        halign: Horizontal alignment of cell content — ``"left"``,
            ``"center"``, or ``"right"`` (default ``"left"``).
        valign: Vertical alignment of cell content — ``"top"``,
            ``"middle"``, or ``"bottom"`` (default ``"top"``).
    """

    overflow:      bool                                    = True
    copy_button:   bool                                    = False
    expand_button: bool                                    = False
    transparent:   bool                                    = False
    halign:        Literal["left", "center", "right"]      = "left"
    valign:        Literal["top", "middle", "bottom"]      = "top"


# ---------------------------------------------------------------------------
# HTMLSlides
# ---------------------------------------------------------------------------

class HTMLSlides:
    """
    Main container for a slideshow.

    Arguments:
        title (str):    The presentation title (required).
        author (str):   The presentation author (optional).
        date (str):     The presentation date (optional, defaults to today).
        version (str):  The presentation version (optional).
        theme (str):    
        custom_css (str | Path | None): Optional path to a custom CSS file to include.
        self_contained (bool): Whether to produce a self-contained HTML file with 
            embedded assets (default: True).
        plugins (list[Plugin]): List of optional plugins to include (default: []).
        slide_defaults (SlideDefaults): Global defaults for slides (default: SlideDefaults()).
        cell_defaults (CellDefaults): Global defaults for cells (default: CellDefaults()).
        autosave (str | None): Optional filename to autosave after each change.
            Use it when iteratively building a presentation to live-preview in
            a browser. If building a large presentation, consider not using
            autosave to avoid excessive writes.
        autosave_level (Literal['slide', 'cell']): Whether to autosave after each
            slide change or cell change (default: 'slide').
            Use 'slide' on presentations with many cells to avoid excessive writes.
            Only relevant if autosave is set to a filename.
        size (tuple[int, int] | None): Fixed slide dimensions in pixels, e.g.
            ``(1366, 768)``. When set, slides become a fixed-size "stage" that is
            scaled with a CSS transform to fit the available area — every element
            (fonts, images, layout) scales together, just like a static PDF.
            When ``None`` (default) the layout is fluid and fills the window
            (current behaviour).
        scale_up (bool): When ``size`` is set, allow scaling beyond the native
            dimensions to fill larger screens. When ``False`` (default) the stage
            never grows past 1:1 — it only shrinks on smaller windows.
        keep_aspect_ratio (bool): When ``size`` is set and ``True`` (default), the
            stage scales uniformly and is letterboxed. When ``False`` the stage
            stretches to fill both dimensions independently (distorts content).
        show_sidebar (bool): Render the slide-navigation sidebar (default
            ``True``). Set to ``False`` for clean single-slide / embeddable files.
        show_toolbar (bool): Render the bottom navigation toolbar (default
            ``True``). Set to ``False`` for clean single-slide / embeddable files.

    Example::

        slides = HTMLSlides(
            title="Q3 Report",
            author="J. Smith",
            theme="default",
            plugins=[Plugin("mathjax"), Plugin("plotly")],
            slide_defaults=SlideDefaults(nrows=2, ncols=2),
            cell_defaults=CellDefaults(expand_button=True),
        )
        slides.add_title("Q3 Report")
        slide = slides.add_slide("Results")
        slide.add_metric(value=98.7, label="Efficiency")
        slides.write("q3-report")
    """

    def __init__(
        self,
        title:          str,
        author:         str                      = "",
        date:           str                      = "",
        version:        str                      = "",
        theme:          str                      = "default",
        custom_css:     str | Path | None        = None,
        self_contained: bool                     = True,
        plugins:        list[Plugin]             = [],
        slide_defaults: SlideDefaults            = SlideDefaults(),   # noqa: B006
        cell_defaults:  CellDefaults             = CellDefaults(),    # noqa: B006
        autosave:       str | None               = None,
        autosave_level: Literal['slide', 'cell'] = 'slide',
        size:              tuple[int, int] | None = None,
        scale_up:          bool                   = False,
        keep_aspect_ratio: bool                   = True,
        show_sidebar:      bool                   = True,
        show_toolbar:      bool                   = True,
    ) -> None:
        self.title          = title
        self.author         = author
        self.date           = date or datetime.date.today().isoformat()
        self.version        = version
        self.theme          = theme
        self.custom_css     = Path(custom_css) if isinstance(custom_css, str) else custom_css
        self.self_contained = self_contained
        self.plugins        = list(plugins)
        self.slide_defaults = slide_defaults
        self.cell_defaults  = cell_defaults
        self.autosave       = autosave
        self.autosave_level = autosave_level
        self.size              = size
        self.scale_up          = scale_up
        self.keep_aspect_ratio = keep_aspect_ratio
        self.show_sidebar      = show_sidebar
        self.show_toolbar      = show_toolbar

        self._slides:   list[Slide] = []
        self._slide_map: dict[Hashable, Slide] = {}
        self._sections: list[dict[str, Any]] = []   # for the automatic TOC
        self._slide_counter = 0

        # Plugin name set for fast membership checks
        self._plugin_names: frozenset[str] = frozenset(p.name for p in self.plugins)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def add_title(
        self,
        title:    str,
        subtitle: str = "",
        notes:    str = "",
    ) -> Slide:
        """Add the cover/title slide."""
        return self._make_slide(
            title=title,
            subtitle=subtitle,
            slide_type="title",
            nrows=1,
            ncols=1,
            row_heights=None,
            col_widths=None,
            notes=notes,
        )

    def add_section(
        self,
        title:      str,
        subtitle:   str  = "",
        level:      int  = 1,
        add_to_toc: bool = True,
        show_toc:   bool = True,
    ) -> Slide:
        """Add a section-divider slide.

        Args:
            title (str): Section heading.
            subtitle (str): Optional secondary text below the heading.
            level (int): Hierarchy depth (1 = top-level, 2 = sub-section, …).
                Higher levels are indented and visually dimmed in the sidebar.
            add_to_toc (bool): Whether to include this section in TOC slides and
                inline section TOCs (default ``True``).
            show_toc (bool): Whether to render an inline TOC on this slide
                highlighting the current section (default ``True``).

        Returns:
            The newly created :class:`~tessera.core.slide.Slide`.
        """
        slide = self._make_slide(
            title=title,
            subtitle=subtitle,
            slide_type="section",
            nrows=1,
            ncols=1,
            row_heights=None,
            col_widths=None,
            notes="",
            level=level,
            show_toc=show_toc,
        )
        if add_to_toc:
            self._sections.append({
                "title":    title,
                "subtitle": subtitle,
                "level":    level,
                "slide_id": slide.slide_id,
            })
        return slide

    def add_toc(
        self,
        title: str = "Table of Contents",
        auto:  bool = True,
    ) -> Slide:
        """Add a Table of Contents slide.

        The TOC is always populated at ``write()`` time so it reflects all
        sections in the deck regardless of call order.

        Args:
            title (str): Slide heading shown in the header bar.
            auto (bool): When ``True`` (default), the TOC is built automatically
                from all ``add_section()`` calls.  When ``False`` the slide
                is rendered with an empty TOC.

        Returns:
            The newly created :class:`~tessera.core.slide.Slide`.
        """
        slide = self._make_slide(
            title=title,
            subtitle="",
            slide_type="toc",
            nrows=1,
            ncols=1,
            row_heights=None,
            col_widths=None,
            notes="",
        )
        slide._auto_toc = auto  # type: ignore[attr-defined]
        return slide

    def add_slide(
        self,
        title:          str,
        subtitle:       str                      = "",
        nrows:          Any                      = _UNSET,
        ncols:          Any                      = _UNSET,
        row_heights:    list[int | str] | None   = _UNSET,
        col_widths:     list[int | str] | None   = _UNSET,
        notes:          str                      = "",
        slide_id:       Hashable | None          = None,
        slide_defaults: SlideDefaults | None     = None,
        cell_defaults:  CellDefaults | None      = None,
    ) -> Slide:
        """Add a standard content slide with an ``nrows x ncols`` cell canvas.

        Args:
            title (str): Slide heading shown in the header bar.
            subtitle (str): Optional secondary heading shown below the title.
            nrows (int): Number of grid rows. Falls back to ``slide_defaults.nrows``
                then ``self.slide_defaults.nrows`` when omitted.
            ncols (int): Number of grid columns. Same fallback chain as ``nrows``.
            row_heights (List[str,...]): Explicit heights for each row (CSS 
                values such as ``"1fr"`` or ``200``). ``None`` lets the grid 
                distribute space evenly. Falls back through the defaults 
                hierarchy when omitted.
            col_widths(List[str,...]): Explicit widths for each column. Same 
                semantics as ``row_heights``.
            notes: Presenter notes attached to this slide (not rendered in the
                slide itself).
            slide_id: Stable identifier for this slide. Auto-generated as
                ``"slide-<n>"`` when ``None``. Raises ``DuplicateSlideError``
                if the id is already in use.
            slide_defaults: Per-call override for grid defaults. Takes
                precedence over ``self.slide_defaults`` but is overridden by
                any explicitly supplied ``nrows`` / ``ncols`` / ``row_heights``
                / ``col_widths`` argument.
            cell_defaults: Per-call override for cell defaults. Takes
                precedence over ``self.cell_defaults`


        Returns:
            The newly created :class:`~tessera.core.slide.Slide`.
        """
        sd = slide_defaults if slide_defaults is not None else self.slide_defaults
        return self._make_slide(
            title=title,
            subtitle=subtitle,
            slide_type="slide",
            nrows=sd.nrows             if nrows       is _UNSET else nrows,
            ncols=sd.ncols             if ncols       is _UNSET else ncols,
            row_heights=sd.row_heights if row_heights is _UNSET else row_heights,
            col_widths=sd.col_widths   if col_widths  is _UNSET else col_widths,
            notes=notes,
            slide_id=slide_id,
            cell_defaults=cell_defaults if cell_defaults is not None else self.cell_defaults,
        )

    def write(
        self,
        filename:     str | Path | None = None,
        open_browser: bool = False,
    ) -> Path:
        """Trigger the Assembler, write ``<filename>.html``, and return the Path."""
        from tessera.core.assembler import Assembler

        if (filename is None) and (self.autosave is not None):
            filename = self.autosave
        elif (filename is None) and (self.autosave is None):
            filename = self.title.replace(" ", "-")

        path = Path(filename).with_suffix(".html")
        assembler = Assembler(self)
        assembler.write(path)

        if open_browser:
            import webbrowser
            webbrowser.open(path.resolve().as_uri())

        return path

    def remove_slide(
            self,
            slide_id:Hashable
        ) -> None:
        """Remove a slide by its ID."""
        if slide_id not in self._slide_map:
            raise KeyError(f"No slide found with ID: {slide_id}")
        slide = self._slide_map.pop(slide_id)
        self._slides.remove(slide)


    def get_slide(
        self,
        slide_id: Hashable,
    ):
        """Get a slide by its ID."""
        if slide_id not in self._slide_map:
            raise KeyError(
                f"No slide found with ID: {slide_id}. Available slide IDs:\n- "
                + '\n- '.join([f'{k}: {v}' for k, v in self._slide_map.items()])
                + '\n')
        return self._slide_map[slide_id]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _make_slide(
        self,
        title:       str,
        subtitle:    str,
        slide_type:  str,
        nrows:       int,
        ncols:       int,
        row_heights: list[int | str] | None,
        col_widths:  list[int | str] | None,
        notes:       str,
        slide_id:    Hashable | None = None,
        cell_defaults: CellDefaults | None = None,
        level:       int  = 1,
        show_toc:    bool = False,
    ) -> Slide:
        self._slide_counter += 1
        
        if slide_id is None:
            slide_id = f"_slide-{self._slide_counter}"
        else:
            slide_id = slide_id
        
        if slide_id in self._slide_map:
            self.remove_slide(slide_id)
        
        slide = Slide(
            slide_id      = slide_id,
            title         = title,
            subtitle      = subtitle,
            slide_type    = slide_type,  # type: ignore[arg-type]
            nrows         = nrows,
            ncols         = ncols,
            row_heights   = row_heights,
            col_widths    = col_widths,
            notes         = notes,
            cell_defaults = cell_defaults,
            plugin_names  = self._plugin_names,
            parent        = self,
            level         = level,
            show_toc      = show_toc,
        )
        self._slides.append(slide)
        self._slide_map[slide_id] = slide

        if self.autosave:
            self.write(self.autosave)

        return slide

    # ------------------------------------------------------------------
    # Read-only properties
    # ------------------------------------------------------------------

    @property
    def slides(self) -> list[Slide]:
        return list(self._slides)

    @property
    def slide_map(self) -> dict[Hashable, Slide]:
        return dict(self._slide_map)

    @property
    def sections(self) -> list[dict]:
        """Read-only list of TOC-registered section metadata dicts."""
        return list(self._sections)

    def __repr__(self) -> str:
        return (
            f"HTMLSlides(title={self.title!r}, slides={len(self._slides)}, "
            f"theme={self.theme!r})"
        )
