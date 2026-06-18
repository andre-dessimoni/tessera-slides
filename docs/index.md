# téssera

**téssera** is a Python library for generating **self-contained, interactive
HTML reports** from data — a single `.html` file with no runtime, ideal for
batch-generated ML and analytics output, dashboards, and technical reports.

Content lives on a grid of typed cells (charts, tables, metrics, code, images,
diagrams). Build a report programmatically, then `write()` it to one portable
file you can email, commit, or serve.


```bash
# Core only
pip install tessera-report


# Full support (Plotly, Pandas, Markdown)
pip install "tessera-report[full]"
```

## Live demo

The report below is an example of the capabilities of téssera.

For a better view, click the &#x26F6; `Fullscreen (F)` button on the bottom toolbar.

```{raw} html
<iframe class="tessera-embed" src="_static/example1.html"
        loading="lazy" allowfullscreen></iframe>
```

## Example of use:

```python
from tessera import Deck, Plugin, SlideDefaults

deck = Deck(
    title="Report",
    plugins=[Plugin("plotly", "cdn"), Plugin("mermaid", "cdn")],
)

deck.add_title("Report", subtitle="Production Engineering")

slide = deck.add_slide("KPIs", nrows=1, ncols=3)

slide.add_metric(value=98.7, label="Efficiency (%)", delta=+2.3)
slide.add_metric(value=142,  label="Defects", delta=-18)
slide.add_metric(value="4.8", label="NPS")

deck.write("report", open_browser=True)
```

---

```{toctree}
:maxdepth: 2
:caption: Guides

sections/quickstart
sections/structure
sections/cell-types
sections/slide-ids
sections/live-editing
sections/layout-templates
sections/demo
```

```{toctree}
:maxdepth: 1
:caption: Reference

sections/api
changelog
```
