"""montin.cells.image_slider — ImageSliderCell"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from montin.cells.base import Cell, CellParams

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
        to_webp: bool = False,
        webp_quality: int | None = None,
        save_source: bool = False,
    ) -> None:
        super().__init__(params)
        self.sources = sources            # paths / urls / base64 / matplotlib Figures
        self.captions = captions
        self.to_webp = to_webp
        self.webp_quality = webp_quality
        self.save_source = save_source
        self.resolved_srcs: list[str] = []  # filled by Assembler

    def render(self, env: "jinja2.Environment") -> str:
        return env.get_template("cell_image_slider.html").render(cell=self)
    
    def __repr__(self) -> str:
        return (
            f"ImageSliderCell(ID={self.params.cell_id!r}, sources={self.sources!r})"
            f" at row={self.params.row}, col={self.params.col}"
        )

