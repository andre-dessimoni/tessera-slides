"""
montin.cells
=============
Sub-package containing all cell types.

Import directly from here::

    from montin.cells import TextCell, TableCell, ImageCell, ...
"""

from montin.cells.base import (
    _UNSET,
    Cell,
    CellParams,
    cell_method,
)
from montin.cells.image import ImageCell
from montin.cells.image_slider import ImageSliderCell
from montin.cells.matplotlib import MatplotlibCell
from montin.cells.misc import (
    CodeCell,
    EmptyCell,
    HtmlCell,
    IframeCell,
    ListCell,
    MermaidCell,
    MetricCell,
)
from montin.cells.plotly import PlotlyCell
from montin.cells.table import TableCell
from montin.cells.tabulator import TabulatorCell
from montin.cells.text import TextCell

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
    "TabulatorCell",
    "ListCell",
    "PlotlyCell",
    "CodeCell",
    "MetricCell",
    "MermaidCell",
    "HtmlCell",
    "IframeCell",
    "EmptyCell",
]
