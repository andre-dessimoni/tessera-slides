# Layout

## Cell grid

Each slide has a CSS Grid canvas of `nrows × ncols`. Cells are placed
automatically from left to right, top to bottom.

Use `col` and `row` to place a cell at a specific position (1-indexed) instead
of the next available slot.

```python
slide = deck.add_slide("Example", nrows=2, ncols=3)

slide.add_text("A")   # row 1, col 1
slide.add_text("B")   # row 1, col 2
slide.add_text("C")   # row 1, col 3
slide.add_text("D")   # row 2, col 1
slide.add_text("E")   # row 2, col 2
slide.add_text("F", row=2, col=3)   # row 2, col 3
```

```{raw} html
<iframe class="tessera-embed" src="../_static/slides/layout.html#grid-basic"
        loading="lazy" allowfullscreen></iframe>
```

---

## Column widths and row heights

By default the grid distributes space evenly. Use `col_widths` and `row_heights`
to set explicit sizes using any valid CSS length (`px`, `%`, `fr`, etc.).

```python
slide = deck.add_slide(
    "Custom sizing",
    nrows=2,
    ncols=2,
    col_widths=["2fr", "1fr"],      # left column twice as wide
    row_heights=["120px", "1fr"],   # first row fixed height
)
```

Mixed units work — `fr` values fill the remaining space after fixed sizes are
applied, the same way they do in native CSS Grid.

```{raw} html
<iframe class="tessera-embed" src="../_static/slides/layout.html#grid-sizing"
        loading="lazy" allowfullscreen></iframe>
```

---

## Spanning cells

Use `colspan` and `rowspan` to stretch a cell across multiple columns or rows.
Use `col` and `row` to place a cell at a specific position (1-indexed) instead
of the next available slot.

```python
slide = deck.add_slide("Spanning", nrows=2, ncols=3)

# Spans columns 1 and 2 of row 1
slide.add_text("Wide header", colspan=2)

# Column 3, row 1
slide.add_metric(value=42, label="KPI")

# Row 2, spans all 3 columns
slide.add_table({'Col a': [1,2,3], 'Col b': [4,5,6]}, colspan=3)

# Explicit position — column 2, row 1, spanning 2 rows
slide.add_image("photo.png", col=2, row=1, rowspan=2)


```

```{raw} html
<iframe class="tessera-embed" src="../_static/slides/layout.html#grid-spanning"
        loading="lazy" allowfullscreen></iframe>
```

---

## Layout templates

`SlideDefaults` and `CellDefaults` can be instantiated independently and passed
per-slide via `slide_defaults` and `cell_defaults`. This lets you define reusable
layout templates and apply them selectively, without changing the global defaults
set on `Deck`.

```python
from tessera import Deck, SlideDefaults, CellDefaults

deck = Deck(title="Template Report")

# Define reusable templates
slide_2x2     = SlideDefaults(ncols=2, nrows=2)
slide_2x1     = SlideDefaults(ncols=2, nrows=1)
centered_cell = CellDefaults(halign="center", valign="middle")

# Apply a layout template and a cell template together
s = deck.add_slide("Results", slide_defaults=slide_2x2, cell_defaults=centered_cell)
for i in range(s.nrows * s.ncols):
    s.add_text(f"Cell {i}")

# Apply only a layout template; cell defaults fall back to the global ones
s = deck.add_slide("Summary", slide_defaults=slide_2x1)
for i in range(s.nrows * s.ncols):
    s.add_text(f"Cell {i}")

deck.write("template_report", open_browser=True)
```

The priority order for each parameter is:

1. **Explicit argument** — value passed directly to `add_slide()` or `add_*()`.
2. **Per-call default** — `slide_defaults` / `cell_defaults` argument on `add_slide()`.
3. **Global default** — `slide_defaults` / `cell_defaults` set on `Deck`.

```{raw} html
<iframe class="tessera-embed" src="../_static/slides/layout.html#templates-results"
        loading="lazy" allowfullscreen></iframe>
```

Use the slide navigator (toggle the sidebar with the &#9776; button or `B`) to
compare the centred *Results* slide with the left-aligned *Summary* slide.
