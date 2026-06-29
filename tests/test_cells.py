"""Tests for individual cell types — construction and parameter storage."""

import pytest

from montin.cells.base import CellParams
from montin.cells.image import ImageCell
from montin.cells.image_slider import ImageSliderCell
from montin.cells.misc import (
    CodeCell,
    EmptyCell,
    HtmlCell,
    IframeCell,
    ListCell,
    MermaidCell,
    MetricCell,
)
from montin.cells.table import TableCell, _detect_separator
from montin.cells.text import TextCell
from montin.exceptions import InvalidDataError


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def params(**kwargs) -> CellParams:
    base = dict(
        cell_id="_cell-1",
        col=1, row=1, colspan=1, rowspan=1,
        caption="", overflow=True, copy_button=False,
        expand_button=False, transparent=False,
    )
    base.update(kwargs)
    return CellParams(**base)


def metric(**kwargs) -> MetricCell:
    """Build a MetricCell, filling the styling args with add_metric's defaults."""
    base = dict(
        value=0, label="", delta=None, delta_label="",
        lower_is_better=False,
        symbol_good="▲", symbol_bad="▼", symbol_neutral="—",
        color_good="#4ade80", color_bad="#f87171", color_neutral="",
        params=params(),
    )
    base.update(kwargs)
    return MetricCell(**base)


# ---------------------------------------------------------------------------
# TextCell
# ---------------------------------------------------------------------------

def test_text_cell_stores_content():
    c = TextCell(content="hello", params=params(), markdown=True)
    assert c.content == "hello"
    assert c.markdown is True


def test_text_cell_markdown_false():
    c = TextCell(content="<b>bold</b>", params=params(), markdown=False)
    assert c.markdown is False


def test_text_cell_params_stored():
    p = params(caption="cap", col=2, row=3)
    c = TextCell(content="x", params=p, markdown=True)
    assert c.params.caption == "cap"
    assert c.col == 2
    assert c.row == 3


# ---------------------------------------------------------------------------
# MetricCell
# ---------------------------------------------------------------------------

def test_metric_stores_value_and_label():
    c = metric(value=99.5, label="Score")
    assert c.value == 99.5
    assert c.label == "Score"
    assert c.delta is None


def test_metric_positive_delta():
    c = metric(value=100, label="L", delta=+5.2, delta_label="vs last month")
    assert c.delta == pytest.approx(5.2)
    assert c.delta_label == "vs last month"


def test_metric_negative_delta():
    c = metric(value=80, label="L", delta=-3)
    assert c.delta == -3


def test_metric_string_value():
    c = metric(value="4.8 ★", label="Rating")
    assert c.value == "4.8 ★"


# ---------------------------------------------------------------------------
# TableCell — _detect_separator
# ---------------------------------------------------------------------------

def test_detect_separator_comma():
    assert _detect_separator("a,b,c\n1,2,3") == ","


def test_detect_separator_tab():
    assert _detect_separator("a\tb\tc\n1\t2\t3") == "\t"


def test_detect_separator_empty():
    assert _detect_separator("") == ","


# ---------------------------------------------------------------------------
# TableCell — CSV
# ---------------------------------------------------------------------------

def test_table_csv_parses_headers_and_rows():
    c = TableCell(data="Name,Age\nAlice,30\nBob,25", separator="auto", index=False, params=params())
    assert c.headers == ["Name", "Age"]
    assert c.rows == [["Alice", "30"], ["Bob", "25"]]


def test_table_tsv_auto_detected():
    c = TableCell(data="Name\tAge\nAlice\t30", separator="auto", index=False, params=params())
    assert c.headers == ["Name", "Age"]
    assert c.rows == [["Alice", "30"]]


def test_table_empty_string():
    c = TableCell(data="", separator="auto", index=False, params=params())
    assert c.headers == []
    assert c.rows == []


# ---------------------------------------------------------------------------
# TableCell — dict
# ---------------------------------------------------------------------------

def test_table_dict():
    data = {"Name": ["Alice", "Bob"], "Score": [95, 87]}
    c = TableCell(data=data, separator="auto", index=False, params=params())
    assert c.headers == ["Name", "Score"]
    assert c.rows[0] == ["Alice", 95]
    assert c.rows[1] == ["Bob", 87]


def test_table_dict_unequal_column_lengths():
    data = {"A": [1, 2, 3], "B": [10]}
    c = TableCell(data=data, separator="auto", index=False, params=params())
    assert len(c.rows) == 3
    assert c.rows[1][1] == ""   # padded
    assert c.rows[2][1] == ""   # padded


# ---------------------------------------------------------------------------
# TableCell — list[list]
# ---------------------------------------------------------------------------

def test_table_list_of_lists():
    data = [["H1", "H2"], [1, 2], [3, 4]]
    c = TableCell(data=data, separator="auto", index=False, params=params())
    assert c.headers == ["H1", "H2"]
    assert c.rows == [[1, 2], [3, 4]]


def test_table_empty_list():
    c = TableCell(data=[], separator="auto", index=False, params=params())
    assert c.headers == []
    assert c.rows == []


def test_table_list_not_nested_raises():
    with pytest.raises(InvalidDataError, match="list\\[list\\]"):
        TableCell(data=["flat", "list"], separator="auto", index=False, params=params())


# ---------------------------------------------------------------------------
# TableCell — invalid type
# ---------------------------------------------------------------------------

def test_table_bad_type_raises():
    with pytest.raises(InvalidDataError, match="Unsupported table data type"):
        TableCell(data=12345, separator="auto", index=False, params=params())


def test_table_reads_csv_file_path(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("Name,Age\nAlice,30\nBob,25", encoding="utf-8")
    c = TableCell(data=str(csv_file), separator="auto", index=False, params=params())
    assert c.headers == ["Name", "Age"]
    assert c.rows == [["Alice", "30"], ["Bob", "25"]]


def test_table_single_line_csv_not_treated_as_path():
    # A one-line CSV string that isn't an existing file stays content, not a path.
    c = TableCell(data="a,b,c", separator="auto", index=False, params=params())
    assert c.headers == ["a", "b", "c"]
    assert c.rows == []


# ---------------------------------------------------------------------------
# TableCell — pandas DataFrame (skip if not installed)
# ---------------------------------------------------------------------------

def test_table_dataframe():
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame({"X": [1, 2], "Y": ["a", "b"]})
    c = TableCell(data=df, separator="auto", index=False, params=params())
    assert c.headers == ["X", "Y"]
    assert c.rows[0] == [1, "a"]


# ---------------------------------------------------------------------------
# ListCell
# ---------------------------------------------------------------------------

def test_list_cell_ordered():
    c = ListCell(items=["A", "B", "C"], ordered=True, params=params())
    assert c.ordered is True
    assert c.items == ["A", "B", "C"]


def test_list_cell_unordered():
    c = ListCell(items=["X"], ordered=False, params=params())
    assert c.ordered is False


# ---------------------------------------------------------------------------
# CodeCell
# ---------------------------------------------------------------------------

def test_code_cell_stores_code_and_language():
    c = CodeCell(code="print('hi')", language="python", params=params())
    assert c.code == "print('hi')"
    assert c.language == "python"


# ---------------------------------------------------------------------------
# MermaidCell
# ---------------------------------------------------------------------------

def test_mermaid_cell_stores_diagram():
    diagram = "flowchart LR\n  A --> B"
    c = MermaidCell(diagram=diagram, params=params())
    assert c.diagram == diagram


# ---------------------------------------------------------------------------
# HtmlCell
# ---------------------------------------------------------------------------

def test_html_cell_stores_content():
    html = "<div>hello</div>"
    c = HtmlCell(content=html, params=params())
    assert c.content == html


# ---------------------------------------------------------------------------
# IframeCell
# ---------------------------------------------------------------------------

def test_iframe_cell_stores_url():
    url = "https://example.com/embed"
    c = IframeCell(url=url, params=params())
    assert c.url == url


# ---------------------------------------------------------------------------
# EmptyCell
# ---------------------------------------------------------------------------

def test_empty_cell_has_params():
    p = params(transparent=True)
    c = EmptyCell(params=p)
    assert c.params.transparent is True


# ---------------------------------------------------------------------------
# CellParams — span properties
# ---------------------------------------------------------------------------

def test_cell_colspan_rowspan_via_params():
    p = params(col=2, row=3, colspan=2, rowspan=3)
    c = HtmlCell(content="x", params=p)
    assert c.colspan == 2
    assert c.rowspan == 3


# ---------------------------------------------------------------------------
# halign / valign — defaults and explicit values
# ---------------------------------------------------------------------------

def test_halign_default_is_left():
    c = TextCell(content="x", params=params(), markdown=True)
    assert c.params.halign == "left"


def test_valign_default_is_top():
    c = TextCell(content="x", params=params(), markdown=True)
    assert c.params.valign == "top"


def test_halign_center_stored():
    p = params(halign="center")
    c = HtmlCell(content="x", params=p)
    assert c.params.halign == "center"


def test_valign_bottom_stored():
    p = params(valign="bottom")
    c = HtmlCell(content="x", params=p)
    assert c.params.valign == "bottom"


def test_halign_right_via_slide(deck):
    s = deck.add_slide("S", nrows=1, ncols=1)
    cell = s.add_text("hi", halign="right")
    assert cell.params.halign == "right"


def test_valign_middle_via_slide(deck):
    s = deck.add_slide("S", nrows=1, ncols=1)
    cell = s.add_metric(value=42, label="KPI", valign="middle")
    assert cell.params.valign == "middle"


def test_halign_center_inherited_from_cell_defaults():
    from montin import CellDefaults, Deck
    deck = Deck(title="X", cell_defaults=CellDefaults(halign="center"))
    s = deck.add_slide("S", nrows=1, ncols=1)
    cell = s.add_text("hello")
    assert cell.params.halign == "center"


def test_valign_bottom_inherited_from_cell_defaults():
    from montin import CellDefaults, Deck
    deck = Deck(title="X", cell_defaults=CellDefaults(valign="bottom"))
    s = deck.add_slide("S", nrows=1, ncols=1)
    cell = s.add_text("hello")
    assert cell.params.valign == "bottom"


def test_per_cell_halign_overrides_default():
    from montin import CellDefaults, Deck
    deck = Deck(title="X", cell_defaults=CellDefaults(halign="center"))
    s = deck.add_slide("S", nrows=1, ncols=2)
    c1 = s.add_text("default")
    c2 = s.add_text("override", halign="right")
    assert c1.params.halign == "center"
    assert c2.params.halign == "right"
