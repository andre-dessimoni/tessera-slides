# Layout

## Cell grid

Each slide has a CSS Grid canvas of `nrows × ncols`. Cells are placed
automatically from left to right, top to bottom.

Use `col` and `row` to place a cell at a specific position (1-indexed) instead
of the next available slot.

```python
slide = slides.add_slide("Example", nrows=2, ncols=3)

slide.add_text("A")   # row 1, col 1
slide.add_text("B")   # row 1, col 2
slide.add_text("C")   # row 1, col 3
slide.add_text("D")   # row 2, col 1
slide.add_text("E")   # row 2, col 2
slide.add_text("F", row=2, col=3)   # row 2, col 3
```

<!-- SCREENSHOT ─ grid-basic.png
Run the code above and capture the resulting slide in a browser.
Six text cells labelled A–F filling a 2×3 grid in reading order.
Save as: docs/_static/img/layout-templates/grid-basic.png
-->

```{figure} ../_static/img/layout-templates/grid-basic.png
:alt: A 2×3 grid with six text cells placed in reading order
:width: 90%

Six cells auto-placed in a 2×3 grid.
```

---

## Column widths and row heights

By default the grid distributes space evenly. Use `col_widths` and `row_heights`
to set explicit sizes using any valid CSS length (`px`, `%`, `fr`, etc.).

```python
slide = slides.add_slide(
    "Custom sizing",
    nrows=2,
    ncols=2,
    col_widths=["2fr", "1fr"],      # left column twice as wide
    row_heights=["120px", "1fr"],   # first row fixed height
)
```

Mixed units work — `fr` values fill the remaining space after fixed sizes are
applied, the same way they do in native CSS Grid.

<!-- SCREENSHOT ─ grid-sizing.png
Run the code above (add a few text cells for visibility) and capture the slide.
The left column should be noticeably wider than the right one, and the first row
shorter/taller than the second depending on the content.
Save as: docs/_static/img/layout-templates/grid-sizing.png
-->

```{figure} ../_static/img/layout-templates/grid-sizing.png
:alt: A 2×2 grid with unequal column widths and row heights
:width: 90%

A 2×2 grid with `col_widths=["2fr", "1fr"]` and `row_heights=["120px", "1fr"]`.
```

---

## Spanning cells

Use `colspan` and `rowspan` to stretch a cell across multiple columns or rows.
Use `col` and `row` to place a cell at a specific position (1-indexed) instead
of the next available slot.

```python
slide = slides.add_slide("Spanning", nrows=2, ncols=3)

# Spans columns 1 and 2 of row 1
slide.add_text("Wide header", colspan=2)

# Column 3, row 1
slide.add_metric(value=42, label="KPI")

# Row 2, spans all 3 columns
slide.add_table({'Col a': [1,2,3], 'Col b': [4,5,6]}, colspan=3)

# Explicit position — column 2, row 1, spanning 2 rows
slide.add_image("photo.png", col=2, row=1, rowspan=2)


```

<!-- SCREENSHOT ─ grid-spanning.png
Build a slide with a clear colspan/rowspan example — e.g. a wide header cell on
top spanning 2 columns, a metric on the right, and a table spanning the full
bottom row. Capture the slide in a browser so the cell boundaries are visible.
Save as: docs/_static/img/layout-templates/grid-spanning.png
-->

```{figure} ../_static/img/layout-templates/grid-spanning.png
:alt: A 2×3 grid with cells spanning multiple columns and rows
:width: 90%

A 2×3 slide with `colspan` and `rowspan` in use.
```

---

## Layout templates

`SlideDefaults` and `CellDefaults` can be instantiated independently and passed
per-slide via `slide_defaults` and `cell_defaults`. This lets you define reusable
layout templates and apply them selectively, without changing the global defaults
set on `HTMLSlides`.

```python
from tessera import HTMLSlides, SlideDefaults, CellDefaults

slides = HTMLSlides(title="Template Report")

# Define reusable templates
slide_2x2     = SlideDefaults(ncols=2, nrows=2)
slide_2x1     = SlideDefaults(ncols=2, nrows=1)
centered_cell = CellDefaults(halign="center", valign="middle")

# Apply a layout template and a cell template together
s = slides.add_slide("Results", slide_defaults=slide_2x2, cell_defaults=centered_cell)
for i in range(s.nrows * s.ncols):
    s.add_text(f"Cell {i}")

# Apply only a layout template; cell defaults fall back to the global ones
s = slides.add_slide("Summary", slide_defaults=slide_2x1)
for i in range(s.nrows * s.ncols):
    s.add_text(f"Cell {i}")

slides.write("template_report", open_browser=True)
```

The priority order for each parameter is:

1. **Explicit argument** — value passed directly to `add_slide()` or `add_*()`.
2. **Per-call default** — `slide_defaults` / `cell_defaults` argument on `add_slide()`.
3. **Global default** — `slide_defaults` / `cell_defaults` set on `HTMLSlides`.

<!-- SCREENSHOT ─ layout-templates.png
Show the tessera presentation in a browser (two slides visible via the slide
navigator):
  • Slide 1 "Results": 2×2 grid, four text cells with "Cell 0" … "Cell 3",
    text centred both horizontally and vertically in each card.
  • Slide 2 "Summary": 2×1 grid, two text cells "Cell 0" and "Cell 1",
    left-aligned (global default).
Save as: docs/_static/img/layout-templates/layout-templates.png
-->

```{figure} ../_static/img/layout-templates/layout-templates.png
:alt: Two slides using different layout templates
:width: 90%

Two slides built from different `SlideDefaults` templates. Slide 1 uses a 2×1 
grid with the global cell defaults; Slide 2 uses a 2×2 grid with centred content
```
