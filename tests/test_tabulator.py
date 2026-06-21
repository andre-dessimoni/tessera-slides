"""Tests for TabulatorCell (interactive tables) and add_tabulator."""

import json

import pytest

from tessera import Deck, Plugins, Security
from tessera.cells.base import CellParams
from tessera.cells.tabulator import TabulatorCell, _safe_fields, _safe_json
from tessera.core.assembler import Assembler
from tessera.exceptions import PluginNotDeclaredError


def params(**kwargs) -> CellParams:
    base = dict(cell_id="_cell-1", col=1, row=1)
    base.update(kwargs)
    return CellParams(**base)


def cell(data, **kwargs) -> TabulatorCell:
    return TabulatorCell(data=data, params=params(), **kwargs)


def config(data, **kwargs) -> dict:
    return cell(data, **kwargs)._build_config()


# ---------------------------------------------------------------------------
# Input parity with add_table (dict / list[list] / DataFrame / CSV / file path)
# ---------------------------------------------------------------------------

def test_dict_input():
    c = config({"Name": ["Alice", "Bob"], "Age": [30, 25]})
    assert [col["title"] for col in c["columns"]] == ["Name", "Age"]
    assert c["data"] == [{"Name": "Alice", "Age": 30}, {"Name": "Bob", "Age": 25}]


def test_list_of_lists_input():
    c = config([["A", "B"], [1, 2], [3, 4]])
    assert c["data"] == [{"A": 1, "B": 2}, {"A": 3, "B": 4}]


def test_csv_string_input():
    c = config("Name,Age\nAlice,30")
    assert c["data"] == [{"Name": "Alice", "Age": "30"}]


def test_csv_file_path_input(tmp_path):
    f = tmp_path / "data.csv"
    f.write_text("Name,Age\nAlice,30\nBob,25", encoding="utf-8")
    c = config(str(f))
    assert c["data"] == [{"Name": "Alice", "Age": "30"}, {"Name": "Bob", "Age": "25"}]


def test_dataframe_input():
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    c = config(df)
    assert c["data"] == [{"x": 1, "y": 3}, {"x": 2, "y": 4}]


# ---------------------------------------------------------------------------
# Field sanitisation + dedupe (titles kept)
# ---------------------------------------------------------------------------

def test_safe_fields_sanitises_and_dedupes():
    assert _safe_fields(["Price ($)", "Price ($)", "1st"]) == ["Price", "Price_2", "c_1st"]


def test_special_char_headers_keep_title_but_safe_field():
    c = config({"Total %": [1]})
    col = c["columns"][0]
    assert col["title"] == "Total %"
    assert col["field"] == "Total"
    assert c["data"] == [{"Total": 1}]


# ---------------------------------------------------------------------------
# Column merge + curated options
# ---------------------------------------------------------------------------

def test_columns_merge_by_title():
    c = config({"price": [1]}, columns=[{"title": "price", "formatter": "money",
                                         "bottomCalc": "sum"}])
    col = c["columns"][0]
    assert col["formatter"] == "money" and col["bottomCalc"] == "sum"
    assert col["field"] == "price"   # field stays the sanitised key


def test_extra_column_not_in_data_is_appended():
    c = config({"a": [1]}, columns=[{"title": "Act", "field": "act",
                                     "formatter": "buttonTick"}])
    titles = [col["title"] for col in c["columns"]]
    assert "Act" in titles


def test_header_filter_sets_per_column():
    c = config({"a": [1], "b": [2]}, header_filter=True)
    assert all(col.get("headerFilter") == "input" for col in c["columns"])


def test_frozen_columns_by_header_name():
    c = config({"a": [1], "b": [2]}, frozen_columns=["a"])
    by_title = {col["title"]: col for col in c["columns"]}
    assert by_title["a"].get("frozen") is True
    assert "frozen" not in by_title["b"]


def test_pagination_group_selectable_land_in_config():
    c = config({"g": [1], "v": [2]}, pagination=25, selectable=True, group_by="g")
    assert c["pagination"] is True and c["paginationSize"] == 25
    assert c["paginationCounter"] == "rows"
    assert c["selectableRows"] is True
    assert c["groupBy"] == "g"   # header name -> field (same here)


def test_options_escape_hatch_wins():
    c = config({"a": [1]}, layout="fitColumns",
               options={"layout": "fitData", "movableRows": True})
    assert c["layout"] == "fitData"      # user option overrides curated default
    assert c["movableRows"] is True


def test_download_filters_to_csv_json():
    c = cell({"a": [1]}, download=["csv", "xlsx", "json"])
    assert c.download == ["csv", "json"]   # xlsx dropped (no SheetJS bundled)


# ---------------------------------------------------------------------------
# Persistence id (stable, includes deck/slide when attached)
# ---------------------------------------------------------------------------

def test_persistence_off_by_default():
    # Off by default: avoids localStorage restoring a stale/incompatible layout
    # (the cause of "works once, breaks on reopen") — opt in per table.
    c = config({"a": [1]})
    assert "persistence" not in c


def test_persistence_opt_in_has_id():
    c = config({"a": [1]}, persistence=True)
    assert c["persistence"] is True and c["persistenceID"]


def test_persistence_id_includes_deck_slide_and_structure():
    deck = Deck(title="Q3", plugins=[Plugins.Tabulator()])
    s = deck.add_slide("S", slide_id="results", nrows=1, ncols=1)
    c = s.add_tabulator({"a": [1]}, persistence=True)
    pid = c._build_config()["persistenceID"]
    assert "Q3" in pid and "results" in pid


def test_persistence_id_changes_when_columns_change():
    # A different column set must yield a different id, so a changed table never
    # restores an incompatible saved layout.
    a = cell({"a": [1], "b": [2]}, persistence=True)._build_config()["persistenceID"]
    b = cell({"a": [1], "c": [2]}, persistence=True)._build_config()["persistenceID"]
    assert a != b


# ---------------------------------------------------------------------------
# Inline-script safety
# ---------------------------------------------------------------------------

def test_safe_json_neutralises_script_close():
    out = _safe_json({"x": "</script><!--"})
    assert "</script>" not in out and "<!--" not in out
    assert "\\u003c" in out


def test_safe_json_is_valid_json():
    out = _safe_json({"x": "a</b>c"})
    assert json.loads(out) == {"x": "a</b>c"}   # escaped <,> restored by the parser


# ---------------------------------------------------------------------------
# End-to-end render
# ---------------------------------------------------------------------------

def test_render_emits_table_and_data():
    deck = Deck(title="T", plugins=[Plugins.Tabulator()])
    deck.add_slide("S", nrows=1, ncols=1).add_tabulator({"Name": ["Alice"]})
    html = Assembler(deck)._render()
    assert 'class="tessera-tabulator"' in html        # the table mount point
    assert 'type="application/json"' in html          # its config block
    assert '"Name": "Alice"' in html or '"Name":"Alice"' in html
    assert "tabulator-tables@6.3.1" in html           # cdn default


def test_dom_ids_unique_across_slides():
    # Regression: cell_id resets per slide, so the table element id must also
    # fold in the slide id — otherwise every slide's first table shares one id
    # and only the first renders.
    import re
    deck = Deck(title="T", plugins=[Plugins.Tabulator()])
    deck.add_slide("A", slide_id="a", nrows=1, ncols=1).add_tabulator({"x": [1]})
    deck.add_slide("B", slide_id="b", nrows=1, ncols=1).add_tabulator({"x": [1]})
    html = Assembler(deck)._render()
    ids = re.findall(r'id="(tab-[^"]+)"', html)   # table divs + their -cfg blocks
    assert ids and len(ids) == len(set(ids)), ids   # all unique (no collision)


def test_add_tabulator_requires_plugin():
    deck = Deck(title="T", plugins=[])
    s = deck.add_slide("S", nrows=1, ncols=1)
    with pytest.raises(PluginNotDeclaredError, match="Plugins.Tabulator()"):
        s.add_tabulator({"a": [1]})


# ---------------------------------------------------------------------------
# Multi-sheet (sheets=)
# ---------------------------------------------------------------------------

def test_sheets_basic_structure():
    c = cell(None, sheets={"Alpha": {"x": [1, 2], "y": [3, 4]}, "Beta": [["p", "q"], [5, 6]]})
    cfg = c._build_config()
    assert cfg["spreadsheet"] is True
    assert cfg["spreadsheetSheetTabs"] is True
    sheets = cfg["spreadsheetSheets"]
    assert len(sheets) == 2
    assert sheets[0]["title"] == "Alpha" and sheets[0]["key"] == "alpha"
    assert sheets[1]["title"] == "Beta"  and sheets[1]["key"] == "beta"


def test_sheets_headers_as_row_zero():
    c = cell(None, sheets={"S": {"Name": ["Alice", "Bob"], "Age": [30, 25]}})
    first_row = c._build_config()["spreadsheetSheets"][0]["data"][0]
    assert first_row == ["Name", "Age"]


def test_sheets_grid_size_includes_buffer():
    c = cell(None, sheets={"S": {"a": [1, 2, 3]}})
    s = c._build_config()["spreadsheetSheets"][0]
    assert s["rows"] == 3 + 1 + 2   # 3 data + 1 header + 2 buffer
    assert s["columns"] == 1 + 2     # 1 col + 2 buffer


def test_sheets_readonly_by_default():
    cfg = cell(None, sheets={"S": {"a": [1]}})._build_config()
    assert cfg["spreadsheetColumnDefinition"]["editor"] is False


def test_sheets_spreadsheet_mode_enables_editing_and_clipboard():
    cfg = cell(None, sheets={"S": {"a": [1]}},
               spreadsheet_mode=True)._build_config()
    assert cfg["spreadsheetColumnDefinition"]["editor"] == "input"
    assert cfg["clipboard"] is True


def test_sheets_row_numbers():
    cfg = cell(None, sheets={"S": {"a": [1]}}, row_numbers=True)._build_config()
    rh = cfg["rowHeader"]
    assert rh["field"] == "_id"
    assert rh["formatter"] == "rownumGlobal"


def test_sheets_accepts_all_data_types(tmp_path):
    f = tmp_path / "data.csv"
    f.write_text("x,y\n1,2", encoding="utf-8")
    cfg = cell(None, sheets={
        "Dict":  {"a": [1]},
        "List":  [["p", "q"], [5, 6]],
        "CSV":   "x,y\n1,2",
        "File":  str(f),
    })._build_config()
    assert len(cfg["spreadsheetSheets"]) == 4


def test_sheets_and_data_raises():
    with pytest.raises(ValueError, match="not both"):
        cell({"a": [1]}, sheets={"S": {"a": [1]}})


def test_neither_data_nor_sheets_raises():
    with pytest.raises(ValueError):
        cell(None)


def test_sheets_tabulator_config_override():
    cfg = cell(None, sheets={"S": {"a": [1]}},
               tabulator_config={"movableColumns": True})._build_config()
    assert cfg["movableColumns"] is True


def test_sheets_renders_in_html():
    deck = Deck(title="T", plugins=[Plugins.Tabulator()])
    deck.add_slide("S", nrows=1, ncols=1).add_tabulator(
        sheets={"A": {"x": [1]}, "B": {"y": [2]}})
    html = Assembler(deck)._render()
    assert "spreadsheetSheetTabs" in html
    assert '"A"' in html and '"B"' in html


def test_bundled_block_external_has_no_external_urls():
    deck = Deck(title="Off", plugins=[Plugins.Tabulator()],
                security=Security(block_external=True))
    deck.add_slide("S", nrows=1, ncols=1).add_tabulator([["A", "B"], [1, 2]])
    html = Assembler(deck)._render()   # raises if any external URL survives
    assert "cdn.jsdelivr.net" not in html
    assert 'class="tessera-tabulator"' in html
