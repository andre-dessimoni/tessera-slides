"""
tessera.cells
=============
Sub-package containing all cell types.

Import directly from here::

    from tessera.cells import TextCell, TableCell, ImageCell, ...
"""

from tessera.cells.base import (
    _UNSET,
    Cell,
    CellParams,
    cell_method,
)
from tessera.cells.image import ImageCell
from tessera.cells.image_slider import ImageSliderCell
from tessera.cells.matplotlib import MatplotlibCell
from tessera.cells.misc import (
    CodeCell,
    EmptyCell,
    HtmlCell,
    IframeCell,
    ListCell,
    MermaidCell,
    MetricCell,
)
from tessera.cells.plotly import PlotlyCell
from tessera.cells.table import TableCell
from tessera.cells.text import TextCell

__all__ = [
    # base
    "_UNSET",
    "Cell",
    "CellParams",
    "cell_method",
    # concrete types
    "TextCell",
    "ImageCell",
    "ImageSliderCell",
    "MatplotlibCell",
    "TableCell",
    "ListCell",
    "PlotlyCell",
    "CodeCell",
    "MetricCell",
    "MermaidCell",
    "HtmlCell",
    "IframeCell",
    "EmptyCell",
]
