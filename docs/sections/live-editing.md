# Live editing

## Notebook preview

In Jupyter (or any frontend that honours `_repr_html_`), returning a deck, a
slide, or a single cell as the last expression in a cell renders an inline,
sandboxed preview — no need to write a file or open a browser:

```python
slides = HTMLSlides(title="Q3 Report", plugins=[Plugin("plotly", "cdn")])
slides.add_title("Q3 Report")
slide = slides.add_slide("KPIs", nrows=1, ncols=2)
cell  = slide.add_metric(value=98.7, label="Efficiency")

slides   # full deck preview (with sidebar / toolbar)
slide    # just this slide, chrome-free
cell     # just this cell
```

Each preview is embedded in an isolated `<iframe>` so the deck's styling and
scripts never leak into the notebook. Slide and cell previews reuse the deck's
theme and plugins.

## Autosave

Pass `autosave` with a filename to have tessera write the HTML file automatically
after each change, so you can live-preview in a browser while building the deck.


```python
presentation = HTMLSlides(
    title="Live Report",
    autosave="report",        # writes report.html after each trigger
    autosave_level="cell",    # trigger: "slide" (default) or "cell"
)
```

`autosave_level` controls how frequently the file is written:

| Level | Trigger | Recommended when |
|---|---|---|
| `"slide"` | After each `add_slide()` | Large presentations with many cells |
| `"cell"` | After each `add_*()` cell call | Small decks or iterative Jupyter workflows |

:::{note}
For large presentations prefer `autosave_level="slide"` to avoid redundant
writes on every cell addition, or keep autosave disabled, manually saving with `.write()` when needed.
:::

## VSCode workflow

A convenient way to use autosave is alongside the
[Live Preview](https://marketplace.visualstudio.com/items?itemName=ms-vscode.live-server)
extension in VSCode. Open the generated `.html` file with **Live Preview** (right-click
the file → *Show Preview*) and it will automatically refresh whenever tessera
rewrites it. This gives you an instant side-by-side view — code on the left,
slides on the right — without leaving the editor, as shown below:

![VSCode-workflow](../_static/img/live-editing/animation.webp)
