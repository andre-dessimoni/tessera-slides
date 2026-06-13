"""tessera.cells.matplotlib — MatplotlibCell"""

from __future__ import annotations

import base64
import io
from typing import TYPE_CHECKING, Literal

from tessera.cells.base import Cell, CellParams

if TYPE_CHECKING:
    import matplotlib.figure
    import jinja2


class MatplotlibCell(Cell):
    """
    Matplotlib figure embedded as a static image.

    The figure is encoded at construction time — the original Figure object is
    not retained, so modifications made after ``add_matplotlib`` have no effect.

    Parameters
    ----------
    fig:
        A ``matplotlib.figure.Figure`` instance.
    dpi:
        Rendering resolution in dots per inch (PNG only; ignored for SVG).
    fmt:
        ``"png"`` (default) embeds a base64 PNG data URI.
        ``"svg"`` embeds an inline SVG string — vector, smaller, no DPI setting.
    lightbox:
        Open in fullscreen lightbox on click.
    """

    def __init__(
        self,
        fig: "matplotlib.figure.Figure",
        dpi: int,
        fmt: Literal["png", "svg"],
        lightbox: bool,
        params: CellParams,
    ) -> None:
        super().__init__(params)
        self.lightbox = lightbox
        self.fmt = fmt
        self.fig = fig
        self.src = self._encode(fig, dpi, fmt)

    @staticmethod
    def _encode(fig: "matplotlib.figure.Figure", dpi: int, fmt: str) -> str:
        buf = io.BytesIO()
        try:
            if fmt == "svg":
                fig.savefig(buf, format="svg", bbox_inches="tight")
                return buf.getvalue().decode("utf-8")
            else:
                fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
                b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                return f"data:image/png;base64,{b64}"
        except Exception as exc:
            from tessera.exceptions import InvalidDataError
            raise InvalidDataError(f"Failed to encode matplotlib figure: {exc}") from exc

    def render(self, env: "jinja2.Environment") -> str:
        if self.fmt == "svg":
            return env.get_template("cell_matplotlib_svg.html").render(cell=self)
        return env.get_template("cell_matplotlib.html").render(cell=self)
    
    def __repr__(self) -> str:
        return (f"MatplotlibCell(ID={self.params.cell_id!r}, fig={self.fig}) "
                f"at row={self.params.row}, col={self.params.col})")
