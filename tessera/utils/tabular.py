"""
tessera.utils.tabular
======================
Shared input normalisation for table-like cells (TableCell, TabulatorCell).

Turns any supported input into a uniform ``(headers, rows)`` pair:

  - ``dict[str, list]``      -> keys = headers, values = columns
  - ``list[list]``           -> first sub-list = headers
  - ``pandas.DataFrame``
  - CSV/TSV ``str``          -> separator auto-detected
  - a path to a CSV/TSV file -> read, then parsed as a CSV/TSV string
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any


def _looks_like_path(data: str) -> bool:
    """Heuristic: a short, single-line string naming an existing file.

    CSV/TSV *content* normally spans multiple lines (header + rows), so only a
    bare path like ``data/sales.csv`` slips through; we additionally require the
    file to actually exist before treating the string as a path.
    """
    if "\n" in data or len(data) > 260:
        return False
    try:
        return Path(data).is_file()
    except (OSError, ValueError):
        return False


def detect_separator(text: str) -> str:
    r"""Detect separator: a tab in the first line -> TSV; otherwise CSV."""
    first_line = text.splitlines()[0] if text else ""
    return "\t" if "\t" in first_line else ","


def normalize_table_data(
    data: Any,
    *,
    separator: str = "auto",
    index: bool = False,
) -> tuple[list[str], list[list[Any]]]:
    r"""Normalise ``data`` into ``(headers, rows)``.

    Args:
        data: a dict of columns, a list of rows (first row = headers), a pandas
            DataFrame, a CSV/TSV string, or a path to a CSV/TSV file.
        separator: ``"auto"`` (detect), ``","`` or ``"\t"`` — only used for
            string / file input.
        index: for a DataFrame, include the index as the first column.

    Returns:
        A ``(headers, rows)`` tuple: ``headers`` is a list of column names and
        ``rows`` a list of row value-lists.

    Raises:
        InvalidDataError: for an unsupported type or a malformed list input.
    """
    from tessera.exceptions import InvalidDataError

    # pandas DataFrame
    try:
        import pandas as pd
        if isinstance(data, pd.DataFrame):
            df = data.reset_index() if index else data
            return list(df.columns.astype(str)), df.values.tolist()
    except ImportError:
        pass

    # dict[str, list] — keys = headers, values = columns
    if isinstance(data, dict):
        headers = list(data.keys())
        cols    = list(data.values())
        length  = max((len(c) for c in cols), default=0)
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
                "A list input expects list[list] where the first sub-list "
                "contains the headers."
            )
        return [str(h) for h in data[0]], [list(r) for r in data[1:]]

    # CSV/TSV string — or a path to a CSV/TSV file
    if isinstance(data, str):
        text = Path(data).read_text(encoding="utf-8") if _looks_like_path(data) else data
        sep = detect_separator(text) if separator == "auto" else separator
        reader = csv.reader(io.StringIO(text.strip()), delimiter=sep)
        rows_raw = list(reader)
        if not rows_raw:
            return [], []
        return rows_raw[0], rows_raw[1:]

    raise InvalidDataError(
        f"Unsupported table data type: {type(data).__name__}. "
        "Use dict, list[list], pandas.DataFrame, a CSV/TSV string, or a file path."
    )
