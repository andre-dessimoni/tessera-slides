"""
tessera.core.slides
====================
Defines ``HTMLSlides``, ``Plugin``, ``SlideDefaults``, and ``CellDefaults``.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Hashable

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
    """Global defaults applied to every ``add_slide()`` call."""

    nrows:       int                      = 1
    ncols:       int                      = 1
    row_heights: list[int | str] | None   = None
    col_widths:  list[int | str] | None   = None


@dataclass
class CellDefaults:
    """Global defaults applied to every ``add_*()`` cell method."""

    overflow:      bool = True
    copy_button:   bool = False
    expand_button: bool = False
    transparent:   bool = False
    halign:        str  = "left"
    valign:        str  = "top"


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
        title:    str,
        subtitle: str = "",
        level:    int = 1,
    ) -> Slide:
        """Add a section-divider slide and register it in the automatic TOC."""
        slide = self._make_slide(
            title=title,
            subtitle=subtitle,
            slide_type="section",
            nrows=1,
            ncols=1,
            row_heights=None,
            col_widths=None,
            notes="",
        )
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
        """
        Add a Table of Contents slide.

        When ``auto=True``, the content is generated from all
        ``add_section()`` calls registered so far.
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
        # The Assembler reads slide._toc_entries to render the TOC
        slide._toc_entries = list(self._sections) if auto else []  # type: ignore[attr-defined]
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
    ) -> Slide:
        """Add a standard content slide with an ``nrows × ncols`` cell canvas.

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
        )

    def write(
        self,
        filename:     str | Path,
        open_browser: bool = False,
    ) -> Path:
        """Trigger the Assembler, write ``<filename>.html``, and return the Path."""
        from tessera.core.assembler import Assembler

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
            cell_defaults = self.cell_defaults,
            plugin_names  = self._plugin_names,
            parent        = self,
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

    def __repr__(self) -> str:
        return (
            f"HTMLSlides(title={self.title!r}, slides={len(self._slides)}, "
            f"theme={self.theme!r})"
        )
