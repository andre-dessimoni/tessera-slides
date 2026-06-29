# Links

`add_text()` renders Markdown, so you add links with the usual
`[text](target)` syntax. Two kinds of target are useful inside a report:

- **External pages** — a full URL: `[Google](https://www.google.com)`.
- **Other slides** — a `#` fragment matching a slide's
  [`slide_id`](slide-ids.md): `[Details](#details)`.

## Linking to another slide

Every slide is reachable by its `slide_id` (see [Slide IDs](slide-ids.md)). Give
the slides you want to link to a stable id, then point a Markdown link at
`#<slide_id>`. Clicking it navigates the deck to that slide — the same mechanism
the table of contents uses.

```python
intro = deck.add_slide("Introduction", slide_id="intro")
intro.add_text("Continue to the [Details slide →](#details).")

details = deck.add_slide("Details", slide_id="details")
details.add_text("[← Back to the Introduction](#intro)")
```

The fragment must match the target's `slide_id` exactly. Auto-generated ids look
like `_slide-2`, so it is clearer to set an explicit `slide_id` on any slide you
intend to link to.

## Linking to an external page

Use a full URL as the target. The link opens in the same tab, replacing the
report — to open it in a new tab instead, drop in a raw `<a>` tag with
`target="_blank"` (inline HTML is allowed inside `add_text()`).

```python
slide.add_text("See [Google](https://www.google.com).")

# Open in a new tab
slide.add_text(
    'See <a href="https://www.google.com" target="_blank" '
    'rel="noopener">Google</a>.'
)
```

:::{note}
Navigation links (`<a href>`) are not external *resource* loads, so they are
allowed even under [`Security(block_external=True)`](security.md) — clicking one
is user-initiated and nothing is fetched until then.
:::

## Full example

The three slides below link to one another and out to the web: slides 1 and 2
link to each other, and slide 3 links to Google. Click the links inside the
preview to navigate between slides.

```python
from montin import Deck

deck = Deck(title="Links")

# Slide 1 — internal link to slide 2
intro = deck.add_slide("Introduction", slide_id="intro")
intro.add_text(
    "### Welcome\n\n"
    "A report can link between its own slides:\n\n"
    "[Go to the Details slide →](#details)",
)

# Slide 2 — internal link back to slide 1
details = deck.add_slide("Details", slide_id="details")
details.add_text(
    "### Details\n\n"
    "[← Back to the Introduction](#intro)",
)

# Slide 3 — external link
resources = deck.add_slide("Resources", slide_id="resources")
resources.add_text(
    "### Resources\n\n"
    "Markdown links to external pages work too — for example, a link to "
    "[Google](https://www.google.com).",
)

deck.write("links.html", open_browser=True)
```

```{raw} html
<iframe class="montin-embed" src="../_static/deck/links.html#intro"
        loading="lazy" allowfullscreen></iframe>
```
