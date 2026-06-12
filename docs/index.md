# téssera

**téssera** is a Python library for generating self-contained HTML slideshows 
— ideal for technical reports, dashboards, and engineering presentations.


```bash
# Core only
pip install tessera-slides


# Full support (Plotly, Pandas, Markdown)
pip install "tessera-slides[full]"
```

## Live demo

The presentaion below is an example of the capabilities of téssera.

For better visualization click on the **Full screen** button on the bottom toolbar

```{raw} html
<div style="
  width: 65vw;
  position: relative;
  padding: 0 1rem;
  box-sizing: border-box;
">
  <iframe
    src="_static/example1.html"
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

```python
from tessera import HTMLSlides, Plugin, SlideDefaults

slides = HTMLSlides(
    title="Q3 Report",
    plugins=[Plugin("plotly", "cdn"), Plugin("mermaid", "cdn")],
)
slides.add_title("Q3 Report", subtitle="Production Engineering")

slide = slides.add_slide("KPIs", nrows=1, ncols=3)
slide.add_metric(value=98.7, label="Efficiency (%)", delta=+2.3)
slide.add_metric(value=142,  label="Defects", delta=-18)
slide.add_metric(value="4.8", label="NPS")

slides.write("report", open_browser=True)
```

---

```{toctree}
:maxdepth: 2
:caption: Guides

quickstart
cell-types
demo
```

```{toctree}
:maxdepth: 1
:caption: Reference

api
changelog
```
