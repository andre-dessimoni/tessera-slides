"""Tests for HTMLSlides, Plugin, SlideDefaults, CellDefaults."""

import datetime

import pytest

from tessera import CellDefaults, HTMLSlides, Plugin, SlideDefaults
from tessera.core.slide import Slide


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_title_stored():
    deck = HTMLSlides(title="My Deck")
    assert deck.title == "My Deck"


def test_date_auto_filled():
    deck = HTMLSlides(title="X")
    assert deck.date == datetime.date.today().isoformat()


def test_date_explicit():
    deck = HTMLSlides(title="X", date="2024-01-15")
    assert deck.date == "2024-01-15"


def test_plugins_stored():
    p1 = Plugin("plotly", "cdn")
    p2 = Plugin("highlight", "cdn")
    deck = HTMLSlides(title="X", plugins=[p1, p2])
    assert len(deck.plugins) == 2
    assert "plotly" in deck._plugin_names
    assert "highlight" in deck._plugin_names
    assert "mermaid" not in deck._plugin_names


def test_plugin_defaults():
    p = Plugin("mathjax")
    assert p.source == "bundled"


def test_slides_list_starts_empty():
    deck = HTMLSlides(title="X")
    assert deck.slides == []


def test_repr():
    deck = HTMLSlides(title="Rep", theme="default")
    r = repr(deck)
    assert "Rep" in r
    assert "default" in r


# ---------------------------------------------------------------------------
# add_title
# ---------------------------------------------------------------------------

def test_add_title_returns_slide():
    deck = HTMLSlides(title="X")
    s = deck.add_title("Cover")
    assert isinstance(s, Slide)
    assert s.slide_type == "title"


def test_add_title_appended():
    deck = HTMLSlides(title="X")
    deck.add_title("Cover")
    assert len(deck.slides) == 1


def test_add_title_grid_is_1x1():
    deck = HTMLSlides(title="X")
    s = deck.add_title("Cover")
    assert s.nrows == 1
    assert s.ncols == 1


# ---------------------------------------------------------------------------
# add_section
# ---------------------------------------------------------------------------

def test_add_section_type():
    deck = HTMLSlides(title="X")
    s = deck.add_section("Section 1")
    assert s.slide_type == "section"


def test_add_section_registers_in_sections():
    deck = HTMLSlides(title="X")
    deck.add_section("Intro", level=1)
    deck.add_section("Methods", level=2)
    assert len(deck.sections) == 2
    assert deck.sections[0]["title"] == "Intro"
    assert deck.sections[1]["level"] == 2


def test_add_section_slide_id_stored():
    deck = HTMLSlides(title="X")
    s = deck.add_section("Sec")
    assert deck.sections[0]["slide_id"] == s.slide_id


# ---------------------------------------------------------------------------
# add_toc
# ---------------------------------------------------------------------------

def test_add_toc_type():
    deck = HTMLSlides(title="X")
    t = deck.add_toc()
    assert t.slide_type == "toc"


def test_add_toc_auto_captures_sections(tmp_path):
    deck = HTMLSlides(title="X")
    deck.add_section("A")
    deck.add_section("B")
    toc = deck.add_toc(auto=True)
    deck.write(tmp_path / "out")
    assert len(toc._toc_entries) == 2
    assert toc._toc_entries[0]["title"] == "A"


def test_add_toc_auto_false_empty(tmp_path):
    deck = HTMLSlides(title="X")
    deck.add_section("A")
    toc = deck.add_toc(auto=False)
    deck.write(tmp_path / "out")
    assert toc._toc_entries == []


def test_add_toc_captures_all_sections(tmp_path):
    deck = HTMLSlides(title="X")
    deck.add_section("Before")
    toc = deck.add_toc(auto=True)
    deck.add_section("After")
    deck.write(tmp_path / "out")
    # TOC is populated at write() time — reflects all sections regardless of order
    assert len(toc._toc_entries) == 2


# ---------------------------------------------------------------------------
# add_slide
# ---------------------------------------------------------------------------

def test_add_slide_returns_slide():
    deck = HTMLSlides(title="X")
    s = deck.add_slide("Results")
    assert isinstance(s, Slide)
    assert s.slide_type == "slide"


def test_add_slide_uses_defaults():
    deck = HTMLSlides(title="X", slide_defaults=SlideDefaults(nrows=3, ncols=4))
    s = deck.add_slide("S")
    assert s.nrows == 3
    assert s.ncols == 4


def test_add_slide_overrides_defaults():
    deck = HTMLSlides(title="X", slide_defaults=SlideDefaults(nrows=3, ncols=4))
    s = deck.add_slide("S", nrows=1, ncols=2)
    assert s.nrows == 1
    assert s.ncols == 2


def test_slide_ids_increment():
    deck = HTMLSlides(title="X")
    s1 = deck.add_title("Cover")
    s2 = deck.add_slide("Slide 1")
    s3 = deck.add_slide("Slide 2")
    ids = [s1.slide_id, s2.slide_id, s3.slide_id]
    assert ids == ["slide-1", "slide-2", "slide-3"]


def test_slides_property_returns_copy():
    deck = HTMLSlides(title="X")
    deck.add_slide("S")
    lst = deck.slides
    lst.append("fake")
    assert len(deck.slides) == 1  # original not mutated


# ---------------------------------------------------------------------------
# CellDefaults propagation
# ---------------------------------------------------------------------------

def test_cell_defaults_propagated(deck):
    deck2 = HTMLSlides(
        title="X",
        cell_defaults=CellDefaults(expand_button=True, overflow=False),
    )
    s = deck2.add_slide("S", nrows=1, ncols=1)
    cell = s.add_text("hello")
    assert cell.params.expand_button is True
    assert cell.params.overflow is False


def test_cell_default_overridden_per_call(deck):
    deck2 = HTMLSlides(
        title="X",
        cell_defaults=CellDefaults(expand_button=True),
    )
    s = deck2.add_slide("S", nrows=1, ncols=1)
    cell = s.add_text("hello", expand_button=False)
    assert cell.params.expand_button is False
