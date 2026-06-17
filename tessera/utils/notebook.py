"""
tessera.utils.notebook
======================
Helpers for rich inline previews in Jupyter notebooks (``_repr_html_``).
"""

from __future__ import annotations

import html as _html

#: Default iframe heights (CSS px) for the three preview granularities.
DECK_PREVIEW_HEIGHT = 600
SLIDE_PREVIEW_HEIGHT = 480
CELL_PREVIEW_HEIGHT = 360


def iframe_srcdoc(full_html: str, height: int = DECK_PREVIEW_HEIGHT) -> str:
    """Wrap a complete HTML document in a sandboxed preview ``<iframe>``.

    The document is embedded via the ``srcdoc`` attribute so its (fixed-position)
    CSS and JS stay isolated from the surrounding notebook. Character references
    round-trip correctly: :func:`html.escape` encodes the document, and the
    browser decodes the ``srcdoc`` attribute before parsing it as the iframe's
    document.

    Args:
        full_html: A complete, standalone HTML document.
        height: Iframe height in CSS pixels.

    Returns:
        An ``<iframe>`` HTML string suitable for returning from ``_repr_html_``.
    """
    escaped = _html.escape(full_html, quote=True)
    return (
        f'<iframe srcdoc="{escaped}" '
        f'style="width:100%;height:{height}px;border:1px solid #ccc;'
        f'border-radius:6px;background:#fff;" '
        f'loading="lazy"></iframe>'
    )


def preview_error(obj: object, exc: Exception) -> str:
    """Fallback markup when a ``_repr_html_`` preview cannot be rendered.

    Args:
        obj: The object whose preview failed (its ``repr`` is shown).
        exc: The exception raised while rendering.

    Returns:
        An escaped ``<pre>`` block — never raises, so a broken preview can't
        break the notebook.
    """
    return (
        f"<pre>{_html.escape(repr(obj))}\n"
        f"[preview unavailable: {_html.escape(str(exc))}]</pre>"
    )
