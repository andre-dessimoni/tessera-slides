"""
tessera.core.plugins
=====================
Optional JavaScript libraries a deck can pull in, and how they are loaded.

Declare the ones you need via the :class:`Plugins` container and pass them to
``Deck(plugins=[...])``::

    from tessera import Deck, Plugins

    Deck(plugins=[
        Plugins.Plotly(),                       # interactive charts
        Plugins.Mermaid(theme="dark"),          # diagrams
        Plugins.Highlight(style="github-dark"), # code highlighting
        Plugins.MathJax(output="svg"),          # LaTeX math
    ])

Nothing is mandatory — declare only what you use. Each plugin can be loaded from
a CDN (``source="cdn"``, the default) or embedded in the file
(``source="bundled"``) for a report that works with no network at all. The deck
sets the default for all of them via ``Deck(plugin_source=...)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Literal


@dataclass
class Plugin:
    """Base class for an optional JS library. Use a :class:`Plugins` subclass.

    Attributes:
        source: ``"cdn"`` to load from a content-delivery network, ``"bundled"``
            to embed the library in the report (fully offline). ``None`` (default)
            inherits the deck-wide ``Deck(plugin_source=...)`` setting.
        version: Pin a specific library version. ``None`` uses the version
            tessera vendors / knows the CDN URL for.
        url: A custom URL to load the library from instead of the default CDN —
            e.g. a company intranet mirror. Only used in ``"cdn"`` mode.
        name: The library identifier (``"plotly"``, ``"mermaid"``, ...). Set by
            each subclass; not meant to be overridden.
    """

    source:  Literal["cdn", "bundled"] | None = None
    version: str | None = None
    url:     str | None = None

    name: ClassVar[str] = ""

    def set_cdn(self, url: str) -> "Plugin":
        """Load this plugin from ``url`` (sets ``source="cdn"``). Returns self.

        Convenience for pointing a plugin at a custom mirror in one call::

            Plugins.MathJax().set_cdn("https://intranet.local/mathjax/tex-svg.js")
        """
        self.source = "cdn"
        self.url = url
        return self


@dataclass
class Plotly(Plugin):
    """Plotly.js — required by ``slide.add_plotly()``."""

    name: ClassVar[str] = "plotly"


@dataclass
class Mermaid(Plugin):
    """Mermaid — required by ``slide.add_mermaid()``.

    Attributes:
        theme: Mermaid theme passed to ``mermaid.initialize`` (e.g. ``"dark"``,
            ``"default"``, ``"forest"``, ``"neutral"``).
    """

    theme: str = "dark"

    name: ClassVar[str] = "mermaid"


@dataclass
class Highlight(Plugin):
    """highlight.js — required by ``slide.add_code()``.

    Attributes:
        style: The highlight.js stylesheet name (e.g. ``"github-dark"``,
            ``"github"``, ``"monokai"``). Selects which CSS theme is loaded.
    """

    style: str = "github-dark"

    name: ClassVar[str] = "highlight"


@dataclass
class MathJax(Plugin):
    """MathJax — renders LaTeX math in ``slide.add_text()``.

    Attributes:
        output: ``"svg"`` (default) renders math as SVG with the glyphs embedded
            in the library, so a bundled deck stays a single offline file.
            ``"chtml"`` uses HTML+CSS with web fonts that are fetched at runtime —
            slightly nicer text selection, but not single-file offline.
    """

    output: Literal["svg", "chtml"] = "svg"

    name: ClassVar[str] = "mathjax"


@dataclass
class Tabulator(Plugin):
    """Tabulator — required by ``slide.add_tabulator()`` (interactive tables).

    Attributes:
        theme: which bundled stylesheet to use. ``"auto"`` (default) follows the
            deck theme — the dark sheet for the ``default``/``dark`` themes, the
            light sheet for ``light``. Force it with ``"light"`` / ``"dark"``.
    """

    theme: Literal["auto", "light", "dark"] = "auto"

    name: ClassVar[str] = "tabulator"


class Plugins:
    """Namespace of the available plugins. Instantiate the one(s) you need::

        Deck(plugins=[Plugins.Plotly(), Plugins.MathJax(source="cdn")])
    """

    Plotly = Plotly
    Mermaid = Mermaid
    Highlight = Highlight
    MathJax = MathJax
    Tabulator = Tabulator
