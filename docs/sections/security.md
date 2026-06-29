# Security & offline use

:::{warning}
**Scope of these measures:** The security options below govern how Montin loads its own JavaScript plugins — CDN integrity checks, CSP, offline guarantees. They say nothing about the trustworthiness of the report itself. An HTML file is editable by anyone; **never open a .html file from a source you don't trust**, regardless of what it claims to be made with.
:::

Montin's purpose is a report that transfers **no data** and works **fully
offline**. A generated `.html` embeds its own styling, scripts, and (when
`self_contained`) its images and libraries, so it can be opened by double-clicking
— no server, no internet, nothing sent anywhere. That makes it a good fit for
sensitive data inside companies that block external traffic.

The `Security` object lets you turn that from a default into an *enforced,
verifiable* property:

```python
from montin import Deck, Plugins, Security

deck = Deck(
    title="Confidential Report",
    plugins=[Plugins.Plotly(), Plugins.Mermaid()],
    security=Security(block_external=True),   # provably offline
)
```

A bare `Deck()` already applies light, always-safe hardening
(`Security()` defaults). The strong guarantee is the opt-in `block_external`.

## What each option means in practice

The web terms below are easy to misjudge, so here is what each one actually does:

| Option | Default | What it does, in plain terms |
|---|---|---|
| `block_external` | `False` | **The hard offline guarantee.** Embeds every library, tells the browser to refuse *any* external request, then re-reads the finished file to prove no external URL remains — erroring instead of writing if one slips through. Forces all plugins to `bundled`. |
| `sri` | `True` | **Tamper-check for CDN libraries.** If a library is loaded from a CDN, the browser checks it against a fingerprint baked into the page; a hacked or intercepted CDN serving altered code won't match, so the browser refuses to run it. No effect on bundled plugins. |
| `no_referrer` | `True` | **Don't leak where the report came from.** If the report is hosted and a user clicks a link in it, the browser won't tell the destination which report URL they came from. (Opening from disk has no referrer anyway.) |
| `noindex` | `False` | **Keep it out of search engines.** If hosted, asks crawlers not to list it, so an internal report doesn't surface on Google. (No effect from disk.) |
| `permissions_policy` | `True` | **Declare no camera / microphone / location use.** See the caveat below. |
| `csp` | `None` | **Advanced.** Provide your own Content-Security-Policy to fully control what the page may load. Overrides the generated one. |

## CSP vs Permissions-Policy: what's actually enforced

Two of these are browser "rule lists," and they are enforced very differently —
this is the part most people get wrong:

- **Content-Security-Policy (CSP)** is a list of where the page may load things
  from. `block_external` sets it to *nowhere external*, so even a stray
  `<script src="https://…">` or a tracking pixel is refused by the browser.
  Crucially, **this works even when you just double-click the file** (`file://`).
  It is the property that actually guarantees no data leaves.

- **Permissions-Policy** is a list for *device features* (camera, microphone,
  location). Browsers only enforce it when a **server** sends it as an HTTP
  response header. Opened straight from disk there is no server, so the `<meta>`
  form is ignored — for a downloaded report it is a documented statement of
  intent, and only becomes a real control when the report is **served** behind a
  host that forwards it as a header.

So: for an offline file, lean on `block_external` (CSP) for the real guarantee;
treat `permissions_policy` and `noindex`/`no_referrer` as good hygiene that pays
off when the report is hosted.

## A provably-offline report

```python
deck = Deck(
    title="Air-gapped Report",
    plugins=[Plugins.Plotly(), Plugins.Mermaid(), Plugins.MathJax()],
    security=Security(block_external=True),
)
deck.add_slide("Results").add_plotly(fig)
deck.write("report")   # raises SecurityError if anything external sneaks in
```

With `block_external=True`:

1. every plugin is embedded (an explicit `source="cdn"` raises, rather than being
   silently overridden);
2. a strict CSP forbids all outbound requests;
3. after rendering, Montin scans the file for external resource URLs and raises
   `SecurityError` — listing them — if any remain.

To confirm by hand: disconnect from the network, open the file, and check that
charts, diagrams, and math still render; the browser's **Network** tab should show
no external requests.

:::{note}
`block_external` only embeds things Montin controls. If *you* add an external
resource — `add_image("https://…")`, a custom CSS `@import url(https://…)`, or an
`<iframe src="https://…">` in your own content — the post-render check catches it
and tells you which one to embed or remove. A plain clickable `<a href="https://…">`
link is allowed: it's navigation, not a load, and transfers nothing until clicked.
:::

## Large files

Embedding libraries makes the file bigger (Plotly ~3.6 MB, Mermaid ~2.9 MB,
MathJax-SVG ~1.5 MB). To keep it down: declare only the plugins you use, or set
`self_contained=False` to write the libraries as local sidecar files instead of
inlining them (still fully offline). See [Plugins](plugins.md).
