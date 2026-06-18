"""
tessera.utils.notebook
======================
Helpers for rich inline previews in Jupyter notebooks (``_repr_html_``).
"""

from __future__ import annotations

import html as _html
import re as _re
import warnings as _warnings

#: Default iframe heights (CSS px) for the three preview granularities.
DECK_PREVIEW_HEIGHT = 600
SLIDE_PREVIEW_HEIGHT = 480
CELL_PREVIEW_HEIGHT = 360


# ---------------------------------------------------------------------------
# Jupyter cell identity — powers ``notebook_unique`` auto-dedup
# ---------------------------------------------------------------------------

def shell_kind() -> str | None:
    """Classify the running interpreter.

    Returns ``"zmq"`` for a Jupyter/ipykernel session, ``"terminal"`` for the
    IPython REPL, or ``None`` for a plain Python script (no IPython at all).
    """
    try:
        from IPython import get_ipython  # type: ignore
    except Exception:
        return None
    ip = get_ipython()
    if ip is None:
        return None
    name = type(ip).__name__
    if name == "TerminalInteractiveShell":
        return "terminal"
    return "zmq"  # ZMQInteractiveShell and any other kernel-backed shell


def current_cell_context() -> tuple[str, str] | None:
    """Return ``(cell_id, msg_id)`` for the executing Jupyter cell, or ``None``.

    ``cell_id`` is stable across re-runs of the same cell; ``msg_id`` changes on
    every execution. Returns ``None`` outside an IPython kernel or when the
    front-end does not attach a cell id to the execute request.
    """
    try:
        from IPython import get_ipython  # type: ignore
    except Exception:
        return None
    ip = get_ipython()
    if ip is None:
        return None
    parent = None
    try:
        parent = ip.get_parent()            # ipykernel >= 6
    except Exception:
        parent = getattr(ip, "parent_header", None)
    if not parent:
        return None
    meta = parent.get("metadata") or {}
    header = parent.get("header") or {}
    cell_id = meta.get("cellId")
    if not cell_id:
        return None
    return (str(cell_id), str(header.get("msg_id") or ""))


def _sanitize_id(s: str) -> str:
    """Reduce a Jupyter cell id to characters safe in an HTML id / filename."""
    return _re.sub(r"[^A-Za-z0-9]", "", s)[:24] or "cell"


def notebook_unique_id(state: dict, prefix: str) -> str | None:
    """Derive a stable ``{prefix}-{cell}-{n}`` id for the current Jupyter cell.

    ``state`` is a per-owner dict (held on a Deck for slides, on a Slide for
    cells). The per-cell counter resets whenever a new ``msg_id`` is seen for a
    cell id, so re-executing a cell reproduces the same id sequence and the
    existing items are replaced in place rather than duplicated.

    Returns ``None`` to signal "fall back to the normal auto-counter id":
    happens only in a plain script (with a warning). In an interactive session
    that cannot supply a cell id, raises ``InvalidDataError``.
    """
    ctx = current_cell_context()
    if ctx is None:
        if shell_kind() is not None:
            from tessera.exceptions import InvalidDataError
            raise InvalidDataError(
                "notebook_unique=True could not determine the Jupyter cell id — "
                "your front-end may not send one. Pass an explicit id instead."
            )
        _warnings.warn(
            "notebook_unique=True has no effect outside a Jupyter notebook; "
            "falling back to an auto-incrementing id.",
            stacklevel=3,
        )
        return None
    cell_id, msg_id = ctx
    rec = state.get(cell_id)
    if rec is None or rec["msg_id"] != msg_id:
        rec = {"msg_id": msg_id, "n": 0}
        state[cell_id] = rec
    n = rec["n"]
    rec["n"] += 1
    return f"{prefix}-{_sanitize_id(cell_id)}-{n}"


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
