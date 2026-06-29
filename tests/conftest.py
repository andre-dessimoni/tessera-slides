import pytest

from montin import CellDefaults, Deck, Plugins, SlideDefaults


@pytest.fixture
def deck():
    """Deck instance with all plugins declared."""
    return Deck(
        title="Test Deck",
        author="Tester",
        plugins=[
            Plugins.Plotly(source="cdn"),
            Plugins.Highlight(source="cdn"),
            Plugins.Mermaid(source="cdn"),
        ],
    )


@pytest.fixture
def slide_2x2(deck):
    return deck.add_slide("Test Slide", nrows=2, ncols=2)


@pytest.fixture
def slide_1x3(deck):
    return deck.add_slide("Wide Slide", nrows=1, ncols=3)
