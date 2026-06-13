"""tessera.cells.image_slider — ImageSliderCell"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from tessera.cells.base import Cell, CellParams

if TYPE_CHECKING:
    import jinja2


class ImageSliderCell(Cell):
    """
    Image carousel with prev/next buttons.
    Clicking an image opens the lightbox with zoom/pan.
    Slider images also appear as lightbox thumbnails.
    """

    _DEFAULT_OVERFLOW = False

    def __init__(
        self,
        sources: list,
        captions: list[str],
        params: CellParams,
    ) -> None:
        super().__init__(params)
        self.sources = sources
        self.captions = captions
        self.resolved_srcs: list[str] = []  # filled by Assembler

    def render(self, env: "jinja2.Environment") -> str:
        return env.get_template("cell_image_slider.html").render(cell=self)
    
    def __repr__(self) -> str:
        return (
            f"ImageSliderCell(ID={self.params.cell_id!r}, sources={self.sources!r})"
            f" at row={self.params.row}, col={self.params.col}"
        )

