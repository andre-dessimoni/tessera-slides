# Live editing

## Notebook preview

In Jupyter (or any frontend that honours `_repr_html_`), returning a deck, a
slide, or a single cell as the last expression in a cell renders an inline,
sandboxed preview — no need to write a file or open a browser:

```python
deck = Deck(title="Q3 Report", plugins=[Plugin("plotly", "cdn")])
deck.add_title("Q3 Report")
slide = deck.add_slide("KPIs", nrows=1, ncols=2)
cell  = slide.add_metric(value=98.7, label="Efficiency")

deck     # full deck preview (with sidebar / toolbar)
slide    # just this slide, chrome-free
cell     # just this cell
```

Each preview is embedded in an isolated `<iframe>` so the deck's styling and
scripts never leak into the notebook. Slide and cell previews reuse the deck's
theme and plugins.

### Laying out cell outputs

Because a single slide previews on its own, you can use tessera purely as a
**layout engine for notebook outputs** — build one slide, drop a few cells onto
its grid, and return it as the cell's last expression. No file is written:

```python
import plotly.express as px
from tessera import Deck, Plugin

deck  = Deck(title="scratch", plugins=[Plugin("plotly", "cdn")])
slide = deck.add_slide("Run 42", nrows=1, ncols=3)

slide.add_metric(value=0.94, label="Accuracy", delta=+0.02)
slide.add_plotly(px.line(df, x="epoch", y="loss"))
slide.add_table(summary_df)

slide   # ← renders a laid-out mini-dashboard as the cell output
```

This gives you a tidy grid of metrics, charts, and tables in a single cell —
handy for experiment summaries — without leaving the notebook.

## Autosave

Pass `autosave` with a filename to have tessera write the HTML file automatically
after each change, so you can live-preview in a browser while building the deck.


```python
deck = Deck(
    title="Live Report",
    autosave="report",        # writes report.html after each trigger
    autosave_level="cell",    # trigger: "slide" (default) or "cell"
)
```

`autosave_level` controls how frequently the file is written:

| Level | Trigger | Recommended when |
|---|---|---|
| `"slide"` | After each `add_slide()` | Large reports with many cells |
| `"cell"` | After each `add_*()` cell call | Small decks or iterative Jupyter workflows |

:::{note}
For large reports prefer `autosave_level="slide"` to avoid redundant
writes on every cell addition, or keep autosave disabled, manually saving with `.write()` when needed.
:::

## VSCode workflow

A convenient way to use autosave is alongside the
[Live Preview](https://marketplace.visualstudio.com/items?itemName=ms-vscode.live-server)
extension in VSCode. Open the generated `.html` file with **Live Preview** (right-click
the file → *Show Preview*) and it will automatically refresh whenever tessera
rewrites it. This gives you an instant side-by-side view — code on the left,
the rendered report on the right — without leaving the editor, as shown below:

![VSCode-workflow](../_static/img/live-editing/animation.webp)
