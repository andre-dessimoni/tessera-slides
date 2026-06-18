# téssera

Build **self-contained, interactive HTML reports** from Python — one file you
can email, commit, or serve, with no runtime and no dependencies on the viewer's
machine. Designed for **batch-generated data and ML output**: loop over your
experiments, runs, or segments and emit a report per iteration.

Content is laid out on a grid of typed cells (charts, tables, metrics, code,
images, diagrams), and the whole deck embeds into a single `.html`.

## Documentation

https://tessera-report.readthedocs.io/

## Installation

```bash
pip install tessera-report

# With Plotly, Pandas and Markdown support:
pip install "tessera-report[full]"
```


## Quick start

```python
from tessera import Deck, Plugin, SlideDefaults, CellDefaults

deck = Deck(
    title="My Report",
    slide_defaults=SlideDefaults(nrows=2, ncols=2),
    cell_defaults=CellDefaults(expand_button=True),
    plugins=[Plugin("plotly", "cdn"), Plugin("mermaid", "cdn")],
)

deck.add_title("My Report", subtitle="Subtitle here")
deck.add_section("1 — Introduction")

slide = deck.add_slide("Results")
slide.add_metric(value=98.7, label="Efficiency (%)", delta=+2.3)
slide.add_text("Text with **markdown** and LaTeX: $E = mc^2$")

deck.write("report", open_browser=True)
```

## Batch generation

The core use case — one report per run, generated in a loop:

```python
for run in experiment_runs:
    deck = Deck(title=f"Run {run.id}")
    slide = deck.add_slide("Metrics", nrows=1, ncols=3)
    slide.add_metric(value=run.accuracy, label="Accuracy", delta=run.delta)
    slide.add_plotly(run.loss_curve)
    deck.write(f"reports/run-{run.id}")
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
