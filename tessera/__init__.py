"""
tessera
=======
Python library for generating self-contained, interactive HTML reports
from data — built for batch-generated ML and analytics output.

Basic usage::

    from tessera import Deck, Plugin, SlideDefaults, CellDefaults

    deck = Deck(title="My Report")
    slide = deck.add_slide("Results", nrows=1, ncols=2)
    slide.add_text("Hello, world!")
    deck.write("my-report")
"""

from importlib.metadata import PackageNotFoundError, version

from tessera.core.deck import CellDefaults, Deck, SlideDefaults
from tessera.core.plugins import (
    Highlight,
    MathJax,
    Mermaid,
    Plotly,
    Plugin,
    Plugins,
    Tabulator,
)
from tessera.core.security import Security
from tessera.exceptions import (
    CellPlacementError,
    HtmlSlidesError,
    InvalidDataError,
    PluginNotDeclaredError,
    SecurityError,
    ThemeNotFoundError,
)

try:
    __version__ = version("tessera-report")
except PackageNotFoundError:  # running from source without installing
    __version__ = "0.0.0.dev"

__all__ = [
    "Deck",
    "Plugin",
    "Plugins",
    "Plotly",
    "Mermaid",
    "Highlight",
    "MathJax",
    "Tabulator",
    "Security",
    "SlideDefaults",
    "CellDefaults",
    "HtmlSlidesError",
    "CellPlacementError",
    "PluginNotDeclaredError",
    "ThemeNotFoundError",
    "InvalidDataError",
    "SecurityError",
    "__version__",
]
