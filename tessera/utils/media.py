"""
tessera.utils.media
===================
Image/figure conversion (WebP) and on-disk asset saving for the "contents
folder" feature. Used by the Assembler at write time and by the matplotlib cell
at construction time.
"""

from __future__ import annotations

import base64
import io
import mimetypes
import os
import re
import warnings
from pathlib import Path


def _pillow():
    try:
        from PIL import Image  # type: ignore
        return Image
    except Exception:
        return None


def data_uri(payload: bytes, mime: str) -> str:
    """Build a ``data:`` URI from raw bytes."""
    b64 = base64.b64encode(payload).decode("ascii")
    return f"data:{mime};base64,{b64}"


def sanitize_name(s: object) -> str:
    """Reduce an arbitrary id to characters safe in a filename."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", str(s)).strip("_") or "asset"


def to_webp_bytes(data: bytes, quality: int | None = None) -> bytes:
    """Convert raster image bytes to WebP. ``quality=None`` => lossless.

    Raises ``RuntimeError`` if Pillow is not installed.
    """
    Image = _pillow()
    if Image is None:
        raise RuntimeError(
            "Pillow is required for WebP conversion. "
            "Install it with: pip install 'tessera-report[image]'"
        )
    img = Image.open(io.BytesIO(data))
    out = io.BytesIO()
    if quality is None:
        img.save(out, format="WEBP", lossless=True)
    else:
        img.save(out, format="WEBP", quality=int(quality))
    return out.getvalue()


def figure_to_payload(
    fig, fmt: str, dpi: int, quality: int | None = None
) -> tuple[bytes, str, str, bool]:
    """Encode a matplotlib figure.

    Returns ``(payload, mime, ext, is_text)``. ``fmt`` is one of
    ``"svg" | "png" | "webp"``; ``webp`` falls back to PNG (with a warning) when
    Pillow is unavailable. ``is_text`` is True only for SVG (embeddable inline).
    """
    fmt = (fmt or "svg").lower()
    buf = io.BytesIO()
    if fmt == "svg":
        fig.savefig(buf, format="svg", bbox_inches="tight")
        return (buf.getvalue(), "image/svg+xml", "svg", True)
    if fmt == "webp":
        if _pillow() is None:
            warnings.warn(
                "Pillow not installed; saving matplotlib figure as PNG instead "
                "of WebP. Install with: pip install 'tessera-report[image]'",
                stacklevel=2,
            )
            fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
            return (buf.getvalue(), "image/png", "png", False)
        fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
        return (to_webp_bytes(buf.getvalue(), quality), "image/webp", "webp", False)
    # png (default raster)
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    return (buf.getvalue(), "image/png", "png", False)


def figure_data_uri(fig, fmt: str, dpi: int, quality: int | None = None) -> str:
    """Encode a matplotlib figure straight to a ``data:`` URI (for ``<img>``)."""
    payload, mime, _ext, _is_text = figure_to_payload(fig, fmt, dpi, quality)
    return data_uri(payload, mime)


def read_image_bytes(source: object) -> tuple[bytes | None, str, str]:
    """Read a *local image file* into ``(bytes, mime, ext)``.

    Returns ``(None, "", "")`` for URLs, ``data:`` URIs, bare base64 strings, or
    missing files — i.e. anything that should be left as-is by the caller.
    """
    s = str(source)
    if s.startswith(("http://", "https://", "data:")):
        return (None, "", "")
    if len(s) > 64 and re.fullmatch(r"[A-Za-z0-9+/=\n]+", s):
        return (None, "", "")
    p = Path(s)
    if not p.exists() or not p.is_file():
        return (None, "", "")
    mime, _ = mimetypes.guess_type(str(p))
    mime = mime or "image/png"
    ext = p.suffix.lstrip(".") or "png"
    return (p.read_bytes(), mime, ext)


def write_asset(contents_dir: Path, stem: str, ext: str, payload: bytes) -> Path:
    """Write ``payload`` to ``contents_dir/<stem>.<ext>``, creating the folder
    lazily on first use. Returns the written path."""
    contents_dir.mkdir(parents=True, exist_ok=True)
    p = contents_dir / f"{stem}.{ext.lstrip('.')}"
    p.write_bytes(payload)
    return p


def rel_url(target: Path, base_dir: Path) -> str:
    """Web-style relative path from ``base_dir`` to ``target`` (forward slashes)."""
    return os.path.relpath(str(target), str(base_dir)).replace("\\", "/")
