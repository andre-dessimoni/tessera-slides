# Plugins

Some cell types need a JavaScript library. You declare the ones you use via the
`Plugins` container and pass them to `Deck(plugins=[...])`:

```python
from montin import Deck, Plugins

deck = Deck(
    title="Report",
    plugins=[
        Plugins.Plotly(),     # interactive charts  → add_plotly()
        Plugins.Mermaid(),    # diagrams            → add_mermaid()
        Plugins.Highlight(),  # code highlighting   → add_code()
        Plugins.MathJax(),    # LaTeX math          → in add_text()
    ],
)
```

| Plugin | Enables | Library |
|---|---|---|
| `Plugins.Plotly()` | `add_plotly()` | Plotly.js |
| `Plugins.Mermaid()` | `add_mermaid()` | Mermaid |
| `Plugins.Highlight()` | `add_code()` | highlight.js |
| `Plugins.MathJax()` | LaTeX in `add_text()` | MathJax |
| `Plugins.Tabulator()` | `add_tabulator()` | Tabulator |

Using a cell without its plugin raises `PluginNotDeclaredError` with the exact
line to add.

## Nothing is mandatory

A plugin is only included if you ask for it. A deck with no plugins ships no
third-party JavaScript at all — handy when a library is blocked by a corporate
firewall or policy, or when you simply don't need it. Declare just what you use.

## CDN or bundled

Each plugin loads one of two ways:

| `source=` | What happens | Trade-off |
|---|---|---|
| `"cdn"` *(default)* | A `<script src="…cdn…">` tag | Small file, needs internet when opened |
| `"bundled"` | The library is embedded in the report | Larger file, works fully offline |

Set it per plugin, or flip the whole deck at once with `plugin_source`:

```python
# Everything embedded → the report opens with no network at all
Deck(plugin_source="bundled", plugins=[Plugins.Plotly(), Plugins.Mermaid()])

# Mostly CDN, but embed the one you need offline
Deck(plugins=[Plugins.Plotly(source="bundled"), Plugins.Mermaid()])
```

Bundled libraries are embedded when the deck is `self_contained` (the default,
giving a single file). With `self_contained=False` they are written next to the
report as local files instead — still no network, just not one file.

:::{note}
For a report that **provably** makes no external request, use
`Security(block_external=True)` — it forces every plugin to bundle and verifies
the output. See [Security & offline use](security.md).
:::

## Per-plugin options

Each plugin carries its own options:

```python
Plugins.Mermaid(theme="forest")        # mermaid theme
Plugins.Highlight(style="github")      # highlight.js stylesheet
Plugins.MathJax(output="svg")          # "svg" (offline-friendly) or "chtml"
Plugins.Tabulator(theme="auto")        # "auto" (follow deck), "light" or "dark"
```

`MathJax(output="svg")` (the default) embeds the glyphs, so a bundled deck stays
a single offline file; `"chtml"` renders with web fonts fetched at runtime.
Only `svg` is vendored for `source="bundled"` — `chtml` is available over CDN,
and bundling it falls back to `svg` (with a warning).

## Pinning a version or a custom source

```python
Plugins.Plotly(version="2.34.0")                       # a specific CDN version
Plugins.Plotly(url="https://intranet.local/plotly.js") # a company mirror
```

`version` / `url` apply to CDN loading. `set_cdn(url)` is shorthand:

```python
Plugins.MathJax().set_cdn("https://intranet.local/mathjax/tex-svg.js")
```

Bundled mode always uses the version Montin vendors; see
[the vendored libraries](#updating-the-bundled-libraries) to change it.

## Updating the bundled libraries

The embedded copies live under `montin/static/vendor/`, one folder per library
(`plotly/`, `mermaid/`, `highlight/`, `mathjax/`) holding its code plus its
`LICENSE` file(s); versions are pinned in `manifest.json`. To refresh or bump a
version (maintainers): edit the version in `manifest.json` and run

```bash
python scripts/update_vendor.py          # download code + licenses, refresh hashes
python scripts/update_vendor.py --check   # verify files, hashes, and licenses
```

The script re-downloads the pinned versions and their license files, recomputes
the integrity hashes, prunes anything no longer referenced, and logs the run in
`vendor/UPDATE_LOG.md`.

### Licensing

The vendored libraries are third-party software under permissive licenses —
Plotly, Mermaid, and Tabulator (MIT), highlight.js (BSD-3-Clause), MathJax
(Apache-2.0). Each
library's license text is shipped next to its code in `vendor/<library>/`. This
matters whenever the libraries are redistributed — including in a `bundled`
report you share — so the attribution travels with them.
