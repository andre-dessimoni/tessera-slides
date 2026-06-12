# téssera

Python library for generating self-contained HTML slideshows for technical 
documents.

## Documentation:

https://tessera-slides.readthedocs.io/

## Installation

```bash
pip install tessera-slides

# With Plotly, Pandas and Markdown support:
pip install "tessera-slides[full]"
```


## Quick start

```python
from tessera import HTMLSlides, Plugin, SlideDefaults, CellDefaults

slides = HTMLSlides(
    title="My Report",
    slide_defaults=SlideDefaults(nrows=2, ncols=2),
    cell_defaults=CellDefaults(expand_button=True),
    plugins=[Plugin("plotly", "cdn"), Plugin("mermaid", "cdn")],
)

slides.add_title("My Report", subtitle="Subtitle here")
slides.add_section("1 — Introduction")

slide = slides.add_slide("Results")
slide.add_metric(value=98.7, label="Efficiency (%)", delta=+2.3)
slide.add_text("Text with **markdown** and LaTeX: $E = mc^2$")

slides.write("report", open_browser=True)
```


## Cell types

| Method | Cell | Description |
|---|---|---|
| `add_text` | TextCell | Markdown + LaTeX (MathJax) |
| `add_metric` | MetricCell | KPI card with value, label and delta |
| `add_table` | TableCell | CSV, dict, list or DataFrame |
| `add_image` | ImageCell | Image with lightbox and zoom/pan |
| `add_image_slider` | ImageSliderCell | Image carousel |
| `add_list` | ListCell | Bullet or numbered list |
| `add_code` | CodeCell | Code with syntax highlighting |
| `add_plotly` | PlotlyCell | Interactive Plotly chart |
| `add_mermaid` | MermaidCell | Declarative diagram (flowchart, etc.) |
| `add_html` | HtmlCell | Raw HTML without escaping |
| `add_iframe` | IframeCell | Embed external content |
| `add_empty` | EmptyCell | Reserves space in the grid |

## Common cell options

All `add_*` methods accept:

```python
slide.add_text(
    "content",
    colspan=2,          # spans 2 columns
    rowspan=1,
    caption="Caption",
    overflow=True,      # internal scroll
    expand_button=True, # expand to fullscreen button
    copy_button=True,   # copy button (CodeCell)
    transparent=True,   # hides cell border and background
)
```

## License

MIT
