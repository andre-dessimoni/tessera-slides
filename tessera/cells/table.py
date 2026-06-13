"""tessera.cells.table — TableCell"""

from __future__ import annotations

import csv
import io
from typing import TYPE_CHECKING, Any, Literal

from tessera.cells.base import Cell, CellParams

if TYPE_CHECKING:
    import jinja2
    import pandas as pd


class TableCell(Cell):
    """
    Data table. Accepts:
      - dict[str, list]        → keys = headers, values = columns
      - list[list]             → first sub-list = headers
      - pd.DataFrame
      - str CSV or TSV         → separator auto-detected
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
        self.headers, self.rows = self._normalize(data, separator, index)

    # ------------------------------------------------------------------
    # Normalisation
    # ------------------------------------------------------------------

    def _normalize(
        self,
        data: Any,
        separator: str,
        index: bool,
    ) -> tuple[list[str], list[list[Any]]]:
        from tessera.exceptions import InvalidDataError

        # pd.DataFrame
        try:
            import pandas as pd
            if isinstance(data, pd.DataFrame):
                df = data.reset_index() if index else data
                return list(df.columns.astype(str)), df.values.tolist()
        except ImportError:
            pass

        # dict[str, list]
        if isinstance(data, dict):
            headers = list(data.keys())
            cols    = list(data.values())
            length  = max(len(c) for c in cols) if cols else 0
            rows    = [
                [col[i] if i < len(col) else "" for col in cols]
                for i in range(length)
            ]
            return headers, rows

        # list[list] — first row = headers
        if isinstance(data, list):
            if not data:
                return [], []
            if not isinstance(data[0], list):
                raise InvalidDataError(
                    "add_table with a list expects list[list] where "
                    "the first sub-list contains the headers."
                )
            return [str(h) for h in data[0]], [list(r) for r in data[1:]]

        # str CSV/TSV
        if isinstance(data, str):
            sep = _detect_separator(data) if separator == "auto" else separator
            reader = csv.reader(io.StringIO(data.strip()), delimiter=sep)
            rows_raw = list(reader)
            if not rows_raw:
                return [], []
            return rows_raw[0], rows_raw[1:]

        raise InvalidDataError(
            f"Unsupported data type in add_table: {type(data).__name__}. "
            "Use dict, list[list], pd.DataFrame, or str (CSV/TSV)."
        )

    def render(self, env: "jinja2.Environment") -> str:
        return env.get_template("cell_table.html").render(cell=self)

    def __repr__(self) -> str:
        return (
            f"TableCell(ID={self.params.cell_id!r}_, "
            f"at row={self.params.row}, col={self.params.col}"
        )

def _detect_separator(text: str) -> str:
    """Detect separator: presence of \\t → TSV; otherwise → CSV."""
    first_line = text.splitlines()[0] if text else ""
    return "\t" if "\t" in first_line else ","
