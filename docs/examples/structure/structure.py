"""Generates docs/_static/title-sections-example.html — the embedded preview for
the "Deck structure" documentation section. Mirrors the "Putting it together"
example in docs/sections/structure.md: a title slide, an auto-populated TOC, and
sections at two levels (some with inline TOCs), plus an untracked appendix.

Run via `make.bat deck` (or any docs build). See docs/conf.py.
"""

from tessera import Deck, Plugin

deck = Deck(
    title="Q3 Platform Report",
    author="A. Dessimoni",
    date="2025-06-01",
    version="3.0",
    plugins=[Plugin("mermaid", "cdn")],
    size=(1280, 720),
    scale_up=True,
    sidebar_collapsed=True,
    theme='light',
)

# -- Title + table of contents ---------------------------------------------
deck.add_title("Q3 Platform Report", subtitle="Platform Engineering")
deck.add_toc()

# -- Infrastructure (level 1) with two sub-sections ------------------------
deck.add_section("Infrastructure")

deck.add_section("Networking", level=2)
slide = deck.add_slide("Network overview", nrows=1, ncols=2)
slide.add_metric(value="12 ms", label="Avg latency", delta=-3, lower_is_better=True)
slide.add_metric(value="99.98 %", label="Uptime", delta=+0.02)

deck.add_section("Storage", level=2)
slide = deck.add_slide("Storage capacity", nrows=1, ncols=2)
slide.add_metric(value="4.2 TB", label="Used")
slide.add_metric(value="12 TB", label="Total")

# -- Model Performance (level 1) -------------------------------------------
deck.add_section("Model Performance")
slide = deck.add_slide("Latency benchmarks", nrows=1, ncols=2, col_widths=["55%", "45%"])
slide.add_table({
    "Model":     ["v2.1", "v2.2", "v3.0"],
    "p50 (ms)":  [41, 38, 29],
    "p99 (ms)":  [120, 110, 88],
})
slide.add_mermaid("""
flowchart LR
    R[Request] --> Q[Queue]
    Q --> W[Worker]
    W --> C[(Cache)]
    W --> M[Model]
    M --> Resp[Response]
""", caption="Serving path")

# -- Appendix: excluded from the TOC and with no inline TOC ----------------
deck.add_section("Appendix", add_to_toc=False, show_toc=False)
slide = deck.add_slide("Methodology", nrows=1, ncols=1)
slide.add_text(
    "### Methodology\n\n"
    "Benchmarks were run on the staging cluster over a 24 h window. "
    "This section is intentionally **excluded from the table of contents** "
    "(`add_to_toc=False`)."
)

deck.write("../../_static/title-sections-example.html")
print("title-sections-example.html written")
