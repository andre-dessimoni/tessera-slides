"""Tests for notebook_unique auto-dedup (Jupyter cell-id based)."""

import pytest

from montin import Deck
from montin.exceptions import InvalidDataError
import montin.utils.notebook as nb


def _patch(monkeypatch, cell_id, msg_id, kind="zmq"):
    monkeypatch.setattr(nb, "current_cell_context", lambda: (cell_id, msg_id))
    monkeypatch.setattr(nb, "shell_kind", lambda: kind)


def test_slide_dedup_across_reruns(monkeypatch):
    deck = Deck(title="x")
    _patch(monkeypatch, "CELL1", "msg-1")
    deck.add_slide("A", notebook_unique=True)
    deck.add_slide("B", notebook_unique=True)
    ids = [s.slide_id for s in deck.slides]
    assert len(deck.slides) == 2

    # Re-running the same Jupyter cell (new msg_id) replaces in place.
    _patch(monkeypatch, "CELL1", "msg-2")
    deck.add_slide("A2", notebook_unique=True)
    deck.add_slide("B2", notebook_unique=True)
    assert len(deck.slides) == 2
    assert [s.slide_id for s in deck.slides] == ids
    assert [s.title for s in deck.slides] == ["A2", "B2"]


def test_cell_dedup_across_reruns(monkeypatch):
    deck = Deck(title="x")
    s = deck.add_slide("S", nrows=2, ncols=2, slide_id="s")
    _patch(monkeypatch, "C", "m1")
    s.add_text("a", notebook_unique=True)
    s.add_text("b", notebook_unique=True)
    assert len(s.cells) == 2

    _patch(monkeypatch, "C", "m2")
    s.add_text("a2", notebook_unique=True)
    s.add_text("b2", notebook_unique=True)
    assert len(s.cells) == 2


def test_distinct_cells_get_distinct_ids(monkeypatch):
    deck = Deck(title="x")
    _patch(monkeypatch, "ONLY", "m1")
    a = deck.add_slide("A", notebook_unique=True)
    b = deck.add_slide("B", notebook_unique=True)
    assert a.slide_id != b.slide_id


def test_script_mode_warns_and_falls_back(monkeypatch):
    monkeypatch.setattr(nb, "current_cell_context", lambda: None)
    monkeypatch.setattr(nb, "shell_kind", lambda: None)
    deck = Deck(title="x")
    with pytest.warns(UserWarning):
        deck.add_slide("A", notebook_unique=True)
    assert len(deck.slides) == 1
    assert deck.slides[0].slide_id == "_slide-1"   # normal counter id


def test_interactive_without_cellid_raises(monkeypatch):
    monkeypatch.setattr(nb, "current_cell_context", lambda: None)
    monkeypatch.setattr(nb, "shell_kind", lambda: "zmq")
    deck = Deck(title="x")
    with pytest.raises(InvalidDataError):
        deck.add_slide("A", notebook_unique=True)


def test_explicit_id_unaffected_by_flag(monkeypatch):
    # An explicit id always wins, regardless of notebook_unique.
    monkeypatch.setattr(nb, "current_cell_context", lambda: None)
    monkeypatch.setattr(nb, "shell_kind", lambda: None)
    deck = Deck(title="x")
    deck.add_slide("A", slide_id="fixed", notebook_unique=True)
    assert deck.slides[0].slide_id == "fixed"
