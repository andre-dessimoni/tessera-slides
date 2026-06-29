"""Tests for font scaling — deck-wide ``fontsize_scale`` and per-cell ``fontscale``."""

from montin import Deck
from montin.core.deck import CellDefaults
from montin.core.assembler import Assembler
from montin.utils.theme_resolver import ThemeResolver


def render(deck: Deck) -> str:
    return Assembler(deck)._render()


# ---------------------------------------------------------------------------
# Deck-level fontsize_scale
# ---------------------------------------------------------------------------

def test_deck_fontsize_scale_defaults_to_one():
    assert Deck(title="D").fontsize_scale == 1.0


def test_deck_fontsize_scale_stored():
    assert Deck(title="D", fontsize_scale=1.3).fontsize_scale == 1.3


def test_deck_fontsize_scale_emitted_on_root():
    deck = Deck(title="D", fontsize_scale=1.3)
    deck.add_slide("S", nrows=1, ncols=1).add_text("hi")
    html = render(deck)
    assert "--deck-font-scale: 1.3" in html
    # the root rule that consumes it is always present
    assert "calc(100% * var(--deck-font-scale))" in html


def test_deck_default_renders_scale_one():
    deck = Deck(title="D")
    deck.add_slide("S", nrows=1, ncols=1).add_text("hi")
    html = render(deck)
    assert "--deck-font-scale: 1.0" in html


# ---------------------------------------------------------------------------
# Per-cell fontscale
# ---------------------------------------------------------------------------

def test_cell_fontscale_defaults_to_one():
    deck = Deck(title="D")
    cell = deck.add_slide("S", nrows=1, ncols=1).add_text("hi")
    assert cell.params.fontscale == 1.0


def test_cell_fontscale_stored_on_params():
    deck = Deck(title="D")
    cell = deck.add_slide("S", nrows=1, ncols=1).add_text("hi", fontscale=1.5)
    assert cell.params.fontscale == 1.5


def test_cell_fontscale_emitted_in_style():
    deck = Deck(title="D")
    deck.add_slide("S", nrows=1, ncols=1).add_text("big", fontscale=1.5)
    html = render(deck)
    assert "--cell-font-scale: 1.5" in html


def test_default_cell_emits_no_cell_var():
    deck = Deck(title="D")
    deck.add_slide("S", nrows=1, ncols=1).add_text("plain")
    html = render(deck)
    assert "--cell-font-scale:" not in html


def test_fontscale_available_on_non_text_cells():
    # The decorator wires fontscale into every add_* method.
    deck = Deck(title="D")
    s = deck.add_slide("S", nrows=1, ncols=2)
    table = s.add_table({"a": [1]}, fontscale=2.0)
    metric = s.add_metric(value=1, label="x", fontscale=0.5)
    assert table.params.fontscale == 2.0
    assert metric.params.fontscale == 0.5


# ---------------------------------------------------------------------------
# CellDefaults
# ---------------------------------------------------------------------------

def test_cell_defaults_fontscale_default():
    assert CellDefaults().fontscale == 1.0


def test_cell_defaults_flow_to_cell():
    deck = Deck(title="D", cell_defaults=CellDefaults(fontscale=1.2))
    cell = deck.add_slide("S", nrows=1, ncols=1).add_text("hi")
    assert cell.params.fontscale == 1.2


def test_explicit_fontscale_overrides_default():
    deck = Deck(title="D", cell_defaults=CellDefaults(fontscale=1.2))
    cell = deck.add_slide("S", nrows=1, ncols=1).add_text("hi", fontscale=2.0)
    assert cell.params.fontscale == 2.0


# ---------------------------------------------------------------------------
# CSS plumbing
# ---------------------------------------------------------------------------

def test_resolved_css_has_both_scale_vars():
    css = ThemeResolver().resolve("default")
    assert "var(--deck-font-scale" in css      # root font-size rule
    assert "var(--cell-font-scale" in css      # content rules


def test_deck_and_cell_scale_compose_in_one_render():
    deck = Deck(title="D", fontsize_scale=1.25)
    deck.add_slide("S", nrows=1, ncols=1).add_text("big", fontscale=1.6)
    html = render(deck)
    assert "--deck-font-scale: 1.25" in html
    assert "--cell-font-scale: 1.6" in html
