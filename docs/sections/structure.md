# Deck structure

Beyond content slides, Montin provides three structural slide types for
organising long reports: **title**, **section**, and **TOC**.

## Title slide

`add_title()` creates the cover slide shown at the start of a deck. It is
centred, displays a large heading, and automatically shows author, date, and
version metadata from the `Deck` constructor.

```python
deck = Deck(
    title="Annual Engineering Report",
    author="A. Dessimoni",
    date="2025-06-01",
    version="2.1",
    theme="default",
)

deck.add_title(
    "Annual Engineering Report",
    subtitle="Platform Performance · H1 2025",
)
```


The `subtitle` appears below the title in a smaller muted style. A decorative
accent bar is drawn under the title block on the default theme.

```{raw} html
<iframe class="montin-embed" src="../_static/deck/title-sections-example.html#title"
        loading="lazy" allowfullscreen></iframe>
```

---

## Section slides

`add_section()` inserts a centred divider slide between groups of content
slides. By default it also shows an inline table of contents that highlights
the current section.

```python
deck.add_section("Data Ingestion")

# sub-section — indented in the sidebar
deck.add_section("Raw pipeline",   level=2)
deck.add_section("Validation",     level=2)

deck.add_section("Model Training")
deck.add_section("Feature store",  level=2)
```

```{raw} html
<iframe class="montin-embed" src="../_static/deck/title-sections-example.html#section_lvl1a"
        loading="lazy" allowfullscreen></iframe>
```


### Section levels

The `level` parameter controls how the section is displayed in the sidebar:

| `level` | Sidebar appearance |
|---|---|
| `1` (default) | Bold, full opacity |
| `2` | Indented, muted colour |
| `3` | Further indented, dimmed |

The same hierarchy is reflected in a section slide's inline TOC: deeper levels
are indented and dimmed, and the current section is highlighted. Below, the
level-2 **Networking** section is the current one:

```{raw} html
<iframe class="montin-embed" src="../_static/deck/title-sections-example.html#section_lvl2aa"
        loading="lazy" allowfullscreen></iframe>
```

### Excluding a section from the TOC

Pass `add_to_toc=False` to create a section divider that does not appear in
TOC slides or inline TOC lists — useful for appendices or internal breaks.

```python
deck.add_section("Appendix", add_to_toc=False)
```

The demo deck's **Appendix** is added this way (and with `show_toc=False`), so it
is a bare divider that never appears in any TOC:

```{raw} html
<iframe class="montin-embed" src="../_static/deck/title-sections-example.html#section_lvl3c"
        loading="lazy" allowfullscreen></iframe>
```

### Inline TOC on section slides

By default (`show_toc=True`) each section slide shows a compact list of all
TOC-registered sections with the current one highlighted. Disable it for a
clean divider with only the title:

```python
deck.add_section("Data Ingestion", show_toc=False)
```

With the default `show_toc=True`, the **Model Performance** section renders the
inline TOC and highlights itself (contrast this with the bare Appendix above):

```{raw} html
<iframe class="montin-embed" src="../_static/deck/title-sections-example.html#section_lvl1b"
        loading="lazy" allowfullscreen></iframe>
```

---

## TOC slide

`add_toc()` inserts a clickable table of contents. The entries are populated at
`write()` time, so the TOC always reflects every section in the deck regardless
of the order you called `add_toc()`.

```python
deck.add_title("Annual Engineering Report")
deck.add_toc()                              # placed early, but populated at write()

deck.add_section("Data Ingestion")
deck.add_slide("Ingestion pipeline", ...)

deck.add_section("Model Training")
deck.add_slide("Training results", ...)

deck.write("report")                        # TOC now lists both sections
```

The entries are clickable — selecting one navigates to that section:

```{raw} html
<iframe class="montin-embed" src="../_static/deck/title-sections-example.html#toc"
        loading="lazy" allowfullscreen></iframe>
```

### Custom title

```python
deck.add_toc("Contents")
```

### Disabling auto-population

Pass `auto=False` to render an empty TOC placeholder (useful as a manual
override or debugging aid):

```python
deck.add_toc(auto=False)
```

---

## Putting it together

```python
from montin import Deck, Plugins

deck = Deck(
    title="Q3 Platform Report",
    author="A. Dessimoni",
    date="2025-06-01",
    version="3.0",
    plugins=[Plugins.Plotly(), Plugins.Mermaid()],
)

deck.add_title("Q3 Platform Report", subtitle="Platform Engineering")
deck.add_toc()

# — Section 1 ——————————————————————————————
deck.add_section("Infrastructure")
deck.add_section("Networking", level=2)

slide = deck.add_slide("Network overview", nrows=1, ncols=2)
slide.add_metric(value="12 ms", label="Avg latency")
slide.add_metric(value="99.98 %", label="Uptime")

deck.add_section("Storage", level=2)

slide = deck.add_slide("Storage capacity", nrows=1, ncols=2)
slide.add_metric(value="4.2 TB", label="Used")
slide.add_metric(value="12 TB",  label="Total")

# — Section 2 ——————————————————————————————
deck.add_section("Model Performance")

slide = deck.add_slide("Latency benchmarks", nrows=1, ncols=2)
# ... add cells ...

# — Appendix (no TOC entry) ————————————————
deck.add_section("Appendix", add_to_toc=False, show_toc=False)

deck.write("q3-report")
```

For a better view, click the &#x26F6; `Fullscreen (F)` button on the bottom toolbar.

```{raw} html
<div style="
  position: relative;
  padding: 0 1rem;
  box-sizing: border-box;
">
  <iframe
    src="../_static/deck/title-sections-example.html"
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