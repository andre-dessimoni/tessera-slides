"""Tests for Slide: auto-cursor, placement errors, _normalize_sizes."""

import pytest

from montin import Deck, Plugin
from montin.core.slide import Slide, _normalize_sizes
from montin.exceptions import CellPlacementError


# ---------------------------------------------------------------------------
# _normalize_sizes
# ---------------------------------------------------------------------------

def test_normalize_sizes_none():
    assert _normalize_sizes(None, 3) == ["1fr", "1fr", "1fr"]


def test_normalize_sizes_empty_list():
    assert _normalize_sizes([], 2) == ["1fr", "1fr"]


def test_normalize_sizes_int():
    assert _normalize_sizes([200, 400], 2) == ["200px", "400px"]


def test_normalize_sizes_str():
    assert _normalize_sizes(["30%", "70%"], 2) == ["30%", "70%"]


def test_normalize_sizes_mixed():
    assert _normalize_sizes([100, "1fr"], 2) == ["100px", "1fr"]


def test_normalize_sizes_padded_short():
    assert _normalize_sizes(["50%"], 3) == ["50%", "1fr", "1fr"]


def test_normalize_sizes_truncated_long():
    result = _normalize_sizes(["10%", "20%", "30%", "40%"], 2)
    assert result == ["10%", "20%"]


# ---------------------------------------------------------------------------
# Auto-cursor positioning
# ---------------------------------------------------------------------------

def test_auto_cursor_fills_row_first(slide_2x2):
    c1 = slide_2x2.add_text("A")
    c2 = slide_2x2.add_text("B")
    assert c1.params.col == 1 and c1.params.row == 1
    assert c2.params.col == 2 and c2.params.row == 1


def test_auto_cursor_wraps_to_next_row(slide_2x2):
    slide_2x2.add_text("A")
    slide_2x2.add_text("B")
    c3 = slide_2x2.add_text("C")
    assert c3.params.col == 1 and c3.params.row == 2


def test_auto_cursor_fills_all_four_cells(slide_2x2):
    cells = [slide_2x2.add_text(str(i)) for i in range(4)]
    positions = [(c.params.col, c.params.row) for c in cells]
    assert positions == [(1, 1), (2, 1), (1, 2), (2, 2)]


def test_colspan_advances_cursor(slide_2x2):
    slide_2x2.add_text("Wide", colspan=2)
    c2 = slide_2x2.add_text("Below")
    assert c2.params.row == 2


def test_rowspan_marks_cells_occupied(slide_2x2):
    # add_metric in col 1 spanning 2 rows; next cell must go to col 2 row 1
    slide_2x2.add_metric(value=10, label="KPI", rowspan=2)
    c2 = slide_2x2.add_text("B")
    assert c2.params.col == 2 and c2.params.row == 1


# ---------------------------------------------------------------------------
# Cell overwrite by cell_id — position preserved, no duplicate
# ---------------------------------------------------------------------------

def test_cell_overwrite_preserves_list_position(slide_1x3):
    slide_1x3.add_text("X", cell_id="x")
    slide_1x3.add_text("Y", cell_id="y")
    slide_1x3.add_text("Z", cell_id="z")
    # Re-run the first cell's code.
    slide_1x3.add_text("X updated", cell_id="x")
    ids = [c.params.cell_id for c in slide_1x3._cells]
    assert ids == ["x", "y", "z"]           # order kept, not moved to end
    assert len(slide_1x3._cells) == 3       # no duplicate
    assert slide_1x3._cell_map["x"].content == "X updated"


# ---------------------------------------------------------------------------
# Manual positioning
# ---------------------------------------------------------------------------

def test_manual_position_accepted(slide_2x2):
    c = slide_2x2.add_text("X", col=2, row=2)
    assert c.params.col == 2 and c.params.row == 2


def test_auto_then_manual_coexist(slide_2x2):
    # auto fills (1,1); manual can then be placed anywhere else
    auto = slide_2x2.add_text("Auto")
    manual = slide_2x2.add_text("Manual", col=2, row=2)
    assert auto.params.col == 1 and auto.params.row == 1
    assert manual.params.col == 2 and manual.params.row == 2


# ---------------------------------------------------------------------------
# Placement errors — CellPlacementError
# ---------------------------------------------------------------------------

def test_col_zero_raises(slide_2x2):
    with pytest.raises(CellPlacementError, match="col=0"):
        slide_2x2.add_text("X", col=0, row=1)


def test_col_exceeds_ncols_raises(slide_2x2):
    with pytest.raises(CellPlacementError, match="col=3"):
        slide_2x2.add_text("X", col=3, row=1)


def test_row_zero_raises(slide_2x2):
    with pytest.raises(CellPlacementError, match="row=0"):
        slide_2x2.add_text("X", col=1, row=0)


def test_row_exceeds_nrows_raises(slide_2x2):
    with pytest.raises(CellPlacementError, match="row=3"):
        slide_2x2.add_text("X", col=1, row=3)


def test_colspan_overflow_raises(slide_2x2):
    with pytest.raises(CellPlacementError, match="colspan=2"):
        slide_2x2.add_text("X", col=2, row=1, colspan=2)


def test_rowspan_overflow_raises(slide_2x2):
    with pytest.raises(CellPlacementError, match="rowspan=2"):
        slide_2x2.add_text("X", col=1, row=2, rowspan=2)


def test_collision_raises(slide_2x2):
    slide_2x2.add_text("First", col=1, row=1)
    with pytest.raises(CellPlacementError, match="already occupied"):
        slide_2x2.add_text("Second", col=1, row=1)


def test_canvas_full_raises(slide_2x2):
    for _ in range(4):
        slide_2x2.add_text("X")
    with pytest.raises(CellPlacementError, match="already full"):
        slide_2x2.add_text("overflow")


# ---------------------------------------------------------------------------
# Slide repr
# ---------------------------------------------------------------------------

def test_slide_repr(slide_2x2):
    r = repr(slide_2x2)
    assert "Test Slide" in r
    assert "2x2" in r
    assert "slide" in r
