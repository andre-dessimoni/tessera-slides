"""Tests for Jupyter previews: _repr_html_ on Deck, Slide, and Cell."""

from montin import Deck, Plugins
from montin.utils.notebook import iframe_srcdoc, preview_error


# ---------------------------------------------------------------------------
# iframe_srcdoc helper
# ---------------------------------------------------------------------------

def test_iframe_srcdoc_wraps_and_escapes():
    out = iframe_srcdoc('<p title="x">a & b</p>', height=300)
    assert out.startswith("<iframe srcdoc=")
    assert "height:300px" in out
    # quotes and ampersands are escaped so the srcdoc attribute stays valid
    assert "&quot;" in out
    assert "&amp;" in out


def test_preview_error_never_raises():
    out = preview_error(object(), ValueError("boom"))
    assert "<pre>" in out
    assert "preview unavailable" in out
    assert "boom" in out


# ---------------------------------------------------------------------------
# Deck._repr_html_
# ---------------------------------------------------------------------------

def test_deck_repr_html_is_iframe():
    deck = Deck(title="Repr Demo")
    deck.add_title("Cover")
    html = deck._repr_html_()
    assert "<iframe" in html
    assert "srcdoc=" in html
    assert "Repr Demo" in html


def test_deck_repr_html_includes_sidebar():
    # Full deck preview keeps the navigation chrome.
    deck = Deck(title="X")
    deck.add_slide("S", nrows=1, ncols=1).add_text("x")
    html = deck._repr_html_()
    assert "&lt;nav id=&quot;sidebar&quot;&gt;" in html


# ---------------------------------------------------------------------------
# Slide._repr_html_
# ---------------------------------------------------------------------------

def test_slide_repr_html_is_iframe_with_title():
    deck = Deck(title="X")
    s = deck.add_slide("Results Dashboard", nrows=1, ncols=1)
    s.add_text("body")
    html = s._repr_html_()
    assert "<iframe" in html
    assert "Results Dashboard" in html


def test_slide_repr_html_is_chromeless():
    # Single-slide preview drops the sidebar/toolbar.
    deck = Deck(title="X")
    s = deck.add_slide("S", nrows=1, ncols=1)
    s.add_text("x")
    html = s._repr_html_()
    assert "&lt;nav id=&quot;sidebar&quot;&gt;" not in html


# ---------------------------------------------------------------------------
# Cell._repr_html_
# ---------------------------------------------------------------------------

def test_cell_repr_html_contains_content():
    deck = Deck(title="X")
    s = deck.add_slide("S", nrows=2, ncols=2)
    cell = s.add_text("UNIQUECELLTEXT")
    html = cell._repr_html_()
    assert "<iframe" in html
    assert "UNIQUECELLTEXT" in html


def test_cell_back_reference_set_on_add():
    deck = Deck(title="X")
    s = deck.add_slide("S", nrows=1, ncols=1)
    cell = s.add_text("x")
    assert cell._slide is s


def test_cell_preview_restores_params():
    deck = Deck(title="X")
    s = deck.add_slide("S", nrows=2, ncols=2)
    cell = s.add_text("hi", col=2, row=2)
    before = (cell.params.col, cell.params.row, cell.params.colspan, cell.params.rowspan)
    cell._repr_html_()   # temporarily moves the cell to (1,1) then restores
    after = (cell.params.col, cell.params.row, cell.params.colspan, cell.params.rowspan)
    assert before == (2, 2, 1, 1)
    assert after == before


def test_cell_preview_renders_at_origin():
    deck = Deck(title="X")
    s = deck.add_slide("S", nrows=3, ncols=3)
    cell = s.add_text("x", col=3, row=3)
    html = cell._repr_html_()
    assert "grid-column: 1 / span 1" in html


def test_plugin_cell_preview_does_not_raise():
    deck = Deck(title="X", plugins=[Plugins.Plotly(source="cdn")])
    px = __import__("plotly.express", fromlist=["scatter"])
    s = deck.add_slide("S", nrows=1, ncols=1)
    fig = px.scatter(x=[1, 2], y=[3, 4], title="PreviewScatterXYZ")
    cell = s.add_plotly(fig)
    html = cell._repr_html_()
    assert "<iframe" in html
    assert "PreviewScatterXYZ" in html
