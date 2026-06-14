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

import plotly.express as px
from tessera import HTMLSlides, Plugin

# 1. Create the deck
slides = HTMLSlides(
    title="Q2 Report",
    author="A. Dessimoni",
    plugins=[Plugin("plotly", "cdn"), Plugin("mermaid", "cdn")],
)

# 2. Add slides

slides = HTMLSlides(title="Template Report", autosave='example', 
                    autosave_level='cell', plugins=[Plugin('mermaid'), Plugin('plotly')])

# Trend chart + breakdown table
slide = slides.add_slide("Trends", nrows=1, ncols=2)

df = px.data.stocks()
fig = px.line(df, x="date", y=["GOOG", "AAPL"])
slide.add_plotly(fig, caption="Weekly close price")

slide.add_table({
    "Component":  ["Motor A", "Motor B", "Pump C",  "Valve D"],
    "Status":     ["OK",      "OK",      "Warning", "OK"],
    "Uptime (%)": [99.1,      97.8,      91.3,      98.6],
})


# KPIs + pipeline diagram
slide = slides.add_slide("Overview", nrows=2, ncols=3)

slide.add_metric(value=98.7, label="Efficiency (%)", delta=+2.3, delta_label="vs Q1")
slide.add_metric(value=142,  label="Incidents",       delta=-18,  lower_is_better=True)
slide.add_metric(value="4.8 s", label="Avg response time")

slide.add_mermaid("""
gantt
    title A Gantt Diagram
    dateFormat YYYY-MM-DD
    section Section
        A task          :a1, 2014-01-01, 30d
        Another task    :after a1, 20d
    section Another
        Task in Another :2014-01-12, 12d
        another task    :24d
""", colspan=2, row=2, col=1)


# 3. Generate the file
slides.write("report", open_browser=True)
```

This generates `report.html` — a single file with no external dependencies.
Click on the `Fullscreen (F)` buttom on the bottom toolbar for better visualization.

```{raw} html
<div style="
  width: 65vw;
  position: relative;
  padding: 0 1rem;
  box-sizing: border-box;
">
  <iframe
    src="../_static/quick-start-report.html"
    style="
      display: block;
      width: 100%;
      height: 600px;
      border: 1px solid var(--color-background-border, #ccc);
      border-radius: 8px;
    "
    loading="lazy"
    allowfullscreen
  ></iframe>
</div>
```


## Cell grid

Each slide has a CSS Grid canvas of `nrows x ncols`. Cells are positioned
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
