"""Tests for the theme system — resolution and CSS generation."""

import pytest

from montin import Deck
from montin.exceptions import ThemeNotFoundError
from montin.utils.theme_resolver import ThemeResolver

SUPPORTED_THEMES = ["default", "light", "dark", "light-blue", "academic", "sobrio"]


# ---------------------------------------------------------------------------
# ThemeResolver
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("theme", SUPPORTED_THEMES)
def test_theme_resolves_without_error(theme):
    css = ThemeResolver().resolve(theme)
    assert isinstance(css, str)
    assert len(css) > 0


def test_unknown_theme_raises():
    with pytest.raises(ThemeNotFoundError, match="does-not-exist"):
        ThemeResolver().resolve("does-not-exist")


# ---------------------------------------------------------------------------
# CSS variable presence
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("theme", SUPPORTED_THEMES)
def test_css_contains_accent_variable(theme):
    css = ThemeResolver().resolve(theme)
    assert "--color-accent" in css


@pytest.mark.parametrize("theme", SUPPORTED_THEMES)
def test_css_contains_surface_variable(theme):
    css = ThemeResolver().resolve(theme)
    assert "--color-surface" in css


# ---------------------------------------------------------------------------
# Theme-specific overrides
# ---------------------------------------------------------------------------

def test_light_theme_overrides_background():
    css = ThemeResolver().resolve("light")
    # Light theme defines a light bg; the last :root wins
    assert "#f4f4f5" in css


def test_dark_theme_overrides_background():
    css = ThemeResolver().resolve("dark")
    assert "#1e1e1e" in css


def test_light_blue_theme_overrides_background():
    css = ThemeResolver().resolve("light-blue")
    assert "#eff6ff" in css


def test_academic_theme_uses_serif_font():
    css = ThemeResolver().resolve("academic")
    assert "Georgia" in css or "serif" in css


def test_sobrio_theme_overrides_background():
    css = ThemeResolver().resolve("sobrio")
    assert "#ffffff" in css


def test_light_theme_delta_colours():
    css = ThemeResolver().resolve("light")
    # Accessible green/red for light backgrounds
    assert "#16a34a" in css
    assert "#dc2626" in css


def test_sobrio_has_no_title_border():
    css = ThemeResolver().resolve("sobrio")
    assert "border-bottom: none" in css


def test_academic_has_thin_title_border():
    css = ThemeResolver().resolve("academic")
    assert "1px solid var(--color-border)" in css


# ---------------------------------------------------------------------------
# End-to-end: write() with each theme
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("theme", SUPPORTED_THEMES)
def test_write_with_theme(tmp_path, theme):
    deck = Deck(title="Test", theme=theme)
    s = deck.add_slide("S", nrows=1, ncols=1)
    s.add_metric(value=99, label="Score", delta=+5, delta_label="vs last")
    out = deck.write(tmp_path / f"out_{theme}", open_browser=False)
    assert out.exists()
    html = out.read_text(encoding="utf-8")
    assert "Test" in html
    assert "Score" in html
