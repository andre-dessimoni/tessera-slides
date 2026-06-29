"""
montin.utils.image_encoder
============================
Base64 encoding for images (self-contained mode).
Supports: local path, URL, already-encoded base64 string.
"""

from __future__ import annotations

import base64
import mimetypes
import re
from pathlib import Path


def encode(source: str | Path) -> str:
    """
    Accepts a local path, URL, or base64 string and returns a data URI
    ready for use in src="..." of an <img> tag.

    Return examples:
        data:image/png;base64,iVBORw0KGgo...
    """
    s = str(source)

    # Already a data URI
    if s.startswith("data:"):
        return s

    # Already plain base64 (no header)
    if _looks_like_base64(s):
        mime = "image/png"  # assume png when no format information is available
        return f"data:{mime};base64,{s}"

    # Remote URL — return as-is (self-contained mode does not download URLs)
    if s.startswith("http://") or s.startswith("https://"):
        return s

    # Local path
    path = Path(s)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    mime, _ = mimetypes.guess_type(str(path))
    mime = mime or "image/png"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def _looks_like_base64(s: str) -> bool:
    """Simple heuristic: long string containing only base64 characters."""
    if len(s) < 64:
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9+/=\n]+", s))
