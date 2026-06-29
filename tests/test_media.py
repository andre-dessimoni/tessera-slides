"""Tests for the media pipeline: WebP, contents folder, figures, plotly export."""

import pytest

from montin import Deck
from montin.cells import ImageSliderCell, MatplotlibCell

mpl = pytest.importorskip("matplotlib")
mpl.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def _fig():
    f = plt.figure()
    plt.plot([0, 1, 2], [1, 3, 2])
    return f


def test_matplotlib_default_is_svg():
    s = Deck(title="x").add_slide("s")
    c = s.add_matplotlib(_fig())
    assert isinstance(c, MatplotlibCell)
    assert c.fmt == "svg" and c.is_svg
    assert c.src.lstrip().startswith("<")          # inline SVG markup


def test_add_image_accepts_figure():
    s = Deck(title="x").add_slide("s")
    assert isinstance(s.add_image(_fig()), MatplotlibCell)


def test_slider_accepts_figure(tmp_path):
    deck = Deck(title="x")
    s = deck.add_slide("s")
    c = s.add_image_slider([_fig(), _fig()])
    assert isinstance(c, ImageSliderCell)
    html = deck.write(tmp_path / "deck").read_text(encoding="utf-8")
    assert "slider-img" in html and len(c.resolved_srcs) == 2


def test_contents_folder_is_lazy(tmp_path):
    deck = Deck(title="p")
    deck.add_slide("s").add_text("hi")
    deck.write(tmp_path / "p")
    assert not (tmp_path / "_p_contents").exists()


def test_save_source_writes_file(tmp_path):
    deck = Deck(title="x")
    deck.add_slide("s").add_matplotlib(_fig(), save_source=True)
    deck.write(tmp_path / "x")
    cdir = tmp_path / "_x_contents"
    assert cdir.exists() and len(list(cdir.iterdir())) == 1


def test_non_self_contained_references_folder(tmp_path):
    deck = Deck(title="x", self_contained=False)
    deck.add_slide("s").add_matplotlib(_fig(), fmt="png", save_source=True)
    html = deck.write(tmp_path / "x").read_text(encoding="utf-8")
    assert "_x_contents/" in html
    assert "data:image/png;base64" not in html      # not inlined


def test_custom_contents_folder(tmp_path):
    deck = Deck(title="x", contents_folder="assets")
    deck.add_slide("s").add_matplotlib(_fig(), save_source=True)
    deck.write(tmp_path / "x")
    assert (tmp_path / "assets").exists()


def test_to_webp_matplotlib():
    pytest.importorskip("PIL")
    s = Deck(title="x").add_slide("s")
    c = s.add_matplotlib(_fig(), to_webp=True)
    assert c.fmt == "webp" and "data:image/webp" in c.src


def test_preview_height_propagates():
    deck = Deck(title="x", preview_height=321)
    s = deck.add_slide("s")
    c = s.add_text("hi")
    assert "height:321px" in deck._repr_html_()
    assert "height:321px" in s._repr_html_()
    assert "height:321px" in c._repr_html_()
