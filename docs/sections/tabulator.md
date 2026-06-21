# Interactive tables

`add_table()` renders a static HTML table. When you want the reader to **sort,
filter, paginate, group, edit, or download** the data, use `add_tabulator()` —
backed by [Tabulator](https://tabulator.info) (bundled, MIT-licensed). It needs
the `Tabulator` plugin:

```python
from tessera import Deck, Plugins

deck = Deck(title="Report", plugins=[Plugins.Tabulator()])
slide = deck.add_slide("Sales")
slide.add_tabulator(df, header_filter=True)
```

It takes the **same inputs as `add_table`** — a `dict` of columns, a `list[list]`
(first row = headers), a pandas `DataFrame`, a CSV/TSV string, or a path to a
CSV/TSV file:

```python
slide.add_tabulator("data/sales.csv")          # a file path
slide.add_tabulator({"Name": [...], "Age": [...]})
slide.add_tabulator(my_dataframe)
```

```{raw} html
<iframe class="tessera-embed" src="../_static/deck/tabulator.html#tabulator"
        loading="lazy" allowfullscreen></iframe>
```

## Common options

These cover the whole table and are passed straight to `add_tabulator()`:

| Option | Default | What it does |
|---|---|---|
| `layout` | `"fitColumns"` | Column sizing: `"fitColumns"`, `"fitData"`, `"fitDataFill"`, `"fitDataStretch"`, `"fitDataTable"`. |
| `responsive` | `True` | Collapse overflowing columns into an expandable row on narrow widths. |
| `pagination` | `None` | Page size (an int) — enables paging and a row counter. |
| `selectable` | `False` | `True` (or a max count) to let the reader select rows. |
| `group_by` | `None` | A column name (or list) to group rows under collapsible headers. |
| `header_filter` | `False` | Add a filter input to every column header. |
| `frozen_columns` | `None` | Column name(s) pinned while scrolling horizontally. |
| `frozen_rows` | `None` | Number of rows pinned to the top. |
| `movable_columns` | `True` | Let the reader drag columns to reorder them. |
| `persistence` | `False` | Remember the reader's sort/filter/column tweaks across reloads (opt-in). |
| `download` | `None` | A list of `"csv"` / `"json"` to show export buttons. |
| `height` | `None` | A fixed height (e.g. `"400px"`) — enables virtual rendering for very large tables. |

:::{note}
**Persistence** is *off* by default. When enabled (`persistence=True`), each
table remembers the reader's sort/filter/column tweaks in the browser
(`localStorage`), keyed by an id derived from the deck title, slide, cell, and
column structure. It's off by default because a saved layout can outlive the
data it described — change the table (or open a different report from disk, where
`file://` shares one storage bucket) and the restored layout no longer matches,
rendering the table broken. Folding the column structure into the key avoids the
worst of that, but opt in only for stable reports a reader returns to.
:::

## Per-column behaviour — `columns=`

Formatters, editors, calculations, freezing, and header filters are *per column*.
Pass `columns=` a list of [Tabulator column definitions](https://tabulator.info/docs/6.3/columns);
each is matched to your data by `title` (or `field`) and merged over the
auto-generated column, so you only specify what you change:

```python
slide.add_tabulator(df, columns=[
    {"title": "Revenue", "formatter": "money",
     "formatterParams": {"symbol": "$"}, "bottomCalc": "sum"},
    {"title": "Margin",  "formatter": "progress", "bottomCalc": "avg"},
    {"title": "Rating",  "formatter": "star", "formatterParams": {"stars": 5}},
    {"title": "Reviewed","formatter": "tickCross", "editor": True},
])
```

```{raw} html
<iframe class="tessera-embed" src="../_static/deck/tabulator.html#formatters"
        loading="lazy" allowfullscreen></iframe>
```

Useful column keys:

- **Formatters**: `money`, `image`, `link`, `html`, `tickCross`, `color`, `star`,
  `progress`, `rownum`, `buttonTick`, `buttonCross` — via `"formatter"` /
  `"formatterParams"`.
- **Editing**: `"editor"` (`"input"`, `"number"`, `True` for a checkbox, …) makes
  a column editable — handy for marking rows already double-checked.
- **Calculations**: `"topCalc"` / `"bottomCalc"` (`"sum"`, `"avg"`, `"min"`,
  `"max"`, `"count"`) add a calculation row.
- **Layout**: `"frozen"`, `"widthGrow"`, `"widthShrink"`, `"headerFilter"`,
  `"headerVertical"`.
- **Column groups** (multi-line headers): nest columns under a group with a
  `"columns"` key: `{"title": "Q1", "columns": [{"title": "Jan", ...}, ...]}`.

### Grouping, editing & download

```{raw} html
<iframe class="tessera-embed" src="../_static/deck/tabulator.html#editing"
        loading="lazy" allowfullscreen></iframe>
```

## Anything else — `options=`

`add_tabulator()` exposes the common cases; the full Tabulator option set is
available through `options=`, a dict merged verbatim into the constructor (and
taking precedence over the keyword options). Use it for the long tail:

```python
slide.add_tabulator(df, options={
    "movableRows":   True,                 # drag to reorder rows
    "history":       True,                 # undo/redo of edits
    "rowHeader":     {"formatter": "rowSelection"},
    "locale":        "pt-br",              # localisation
    "langs":         {"pt-br": {...}},
})
```

Spreadsheet mode, multi-sheet workbooks, nested tables, range selection, and
interaction history are all reachable this way — see the
[Tabulator docs](https://tabulator.info/docs/6.3). Excel (`xlsx`) download needs
an extra library (SheetJS) that tessera does not bundle, so `download` covers
`csv` and `json` only.

## Offline & themes

Like every plugin, Tabulator is bundled (offline) or loaded from a CDN — see
[Plugins](plugins.md) and [Security & offline use](security.md). It works under
`Security(block_external=True)`. The table styling follows the deck theme
automatically; `Plugins.Tabulator(theme="light")` / `"dark"` forces a specific
look.
