"""tessera.cells.table — TableCell"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from tessera.cells.base import Cell, CellParams
from tessera.utils.tabular import detect_separator as _detect_separator  # noqa: F401 (back-compat re-export)
from tessera.utils.tabular import normalize_table_data

if TYPE_CHECKING:
    import jinja2
    import pandas as pd


class TableCell(Cell):
    """
    Static HTML data table. Accepts:
      - dict[str, list]        → keys = headers, values = columns
      - list[list]             → first sub-list = headers
      - pd.DataFrame
      - str CSV or TSV         → separator auto-detected
      - path to a CSV/TSV file → read, then parsed as above
    """

    def __init__(
        self,
        data: "dict[str, Any] | list[list[Any]] | pd.DataFrame | str",
        separator: Literal["auto", ",", "\t"],
        index: bool,
        params: CellParams,
    ) -> None:
        super().__init__(params)
        self.separator = separator
        self.index     = index
        self.headers, self.rows = normalize_table_data(
            data, separator=separator, index=index)

    def render(self, env: "jinja2.Environment") -> str:
        return env.get_template("cell_table.html").render(cell=self)

    def __repr__(self) -> str:
        return (
            f"TableCell(ID={self.params.cell_id!r}_, "
            f"at row={self.params.row}, col={self.params.col}"
        )
