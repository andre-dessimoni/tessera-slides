# Quick start

## Installation

```bash
# Core only
pip install tessera-slides


# Full support (Plotly, Pandas, Markdown)
pip install "tessera-slides[full]"
```

## Basic structure

Every slideshow follows the same pattern:

```python
from tessera import HTMLSlides, Plugin, SlideDefaults, CellDefaults

# 1. Create the deck
slides = HTMLSlides(
    title="My Report",
    author="A. Dessimoni",
    date="2026-06-09",
    theme="default",
    self_contained=True,           # embed images as base64
    slide_defaults=SlideDefaults(nrows=2, ncols=2),
    cell_defaults=CellDefaults(expand_button=True),
    plugins=[Plugin("plotly", "cdn"), Plugin("mermaid", "cdn")],
)

# 2. Add slides
slides.add_title("My Report", subtitle="Subtitle here")
slides.add_section("1 — Introduction")

slide = slides.add_slide("Results")
slide.add_metric(value=98.7, label="Efficiency (%)", delta=+2.3)
slide.add_text("Text with **markdown** and LaTeX: $E = mc^2$")

# 3. Generate the file
slides.write("report", open_browser=True)
```

This generates `report.html` — a single file with no external dependencies.

## Cell grid

Each slide has a CSS Grid canvas of `nrows × ncols`. Cells are positioned
automatically from left to right, top to bottom.

```python
slide = slides.add_slide("Example", nrows=2, ncols=3)

# Spans columns 1 and 2 of row 1
slide.add_text("Wide text", colspan=2)

# Column 3 of row 1
slide.add_metric(value=42, label="KPI")

# Row 2, spans all 3 columns
slide.add_table(csv_data, colspan=3)
```

To position manually:

```python
slide.add_image("photo.png", col=2, row=1, rowspan=2)
```

## Plugins

Some cell types require a plugin declared on `HTMLSlides`:

| Plugin | Cells |
|---|---|
| `Plugin("plotly", "cdn")` | `add_plotly()` |
| `Plugin("highlight", "cdn")` | `add_code()` |
| `Plugin("mermaid", "cdn")` | `add_mermaid()` |
| `Plugin("mathjax", "cdn")` | LaTeX in `add_text()` |

## Common cell options

All `add_*` methods accept:

| Parameter | Type | Description |
|---|---|---|
| `colspan` | `int` | Number of columns spanned |
| `rowspan` | `int` | Number of rows spanned |
| `col`, `row` | `int` | Manual position (1-indexed) |
| `caption` | `str` | Caption below the cell |
| `overflow` | `bool` | Internal scroll when content overflows |
| `expand_button` | `bool` | Button to expand cell to full screen |
| `copy_button` | `bool` | Button to copy cell content |
| `transparent` | `bool` | Hide border and background |

## Global defaults

Use `CellDefaults` and `SlideDefaults` to avoid repetition:

```python
slides = HTMLSlides(
    title="...",
    slide_defaults=SlideDefaults(nrows=2, ncols=2),
    cell_defaults=CellDefaults(
        expand_button=True,
        overflow=True,
        transparent=False,
    ),
)
```
