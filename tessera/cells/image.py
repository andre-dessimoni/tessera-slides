"""tessera.cells.image — ImageCell"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from tessera.cells.base import Cell, CellParams

if TYPE_CHECKING:
    import jinja2


class ImageCell(Cell):
    """
    Image with lightbox (zoom/pan) and thumbnails for all images on the slide.
    Accepts a local path, URL, or base64 string.
    Effective overflow default: False (image fits the cell).
    """

    def __init__(
        self,
        source: str | Path,
        lightbox: bool,
        params: CellParams,
        to_webp: bool = False,
        webp_quality: int | None = None,
        save_source: bool = False,
    ) -> None:
        super().__init__(params)
        self.lightbox = lightbox
        self.to_webp = to_webp
        self.webp_quality = webp_quality
        self.save_source = save_source
        # Resolve relative path against the caller's cwd immediately,
        # before the cwd can change. URLs and base64 strings are left as-is.
        s = str(source)
        if not s.startswith(("http://", "https://", "data:")) and not _looks_like_base64(s):
            self.source = Path(s).resolve()
        else:
            self.source = s
        self.resolved_src: str = ""  # filled by Assembler before render

    def render(self, env: "jinja2.Environment") -> str:
        return env.get_template("cell_image.html").render(cell=self)
    
    def __repr__(self) -> str:
        return (
            f"ImageCell(ID={self.params.cell_id!r}, source={str(self.source)!r})"
            f" at row={self.params.row}, col={self.params.col}"
        )


def _looks_like_base64(s: str) -> bool:
    import re
    return len(s) > 64 and bool(re.fullmatch(r"[A-Za-z0-9+/=\n]+", s))
