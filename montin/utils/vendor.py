"""
montin.utils.vendor
====================
Resolves a declared :class:`~montin.core.plugins.Plugin` into the concrete
``<script>`` / ``<link>`` assets the template should emit, honouring the chosen
loading mode (CDN vs bundled) and the vendor ``manifest.json``.

The :class:`~montin.core.assembler.Assembler` owns all file IO (reading the
inlined text, copying sidecar files); this module is pure given the manifest, so
it is straightforward to unit-test.

An *asset* is a plain dict the template renders directly:

    {"type": "js"|"css", "mode": "inline"|"src"|"copy",
     "path": Path,            # inline / copy: the vendored file on disk
     "filename": str,         # copy: target name next to the report
     "url": str,              # src: where the browser loads it from
     "integrity": str|None}   # src: SRI hash when we can vouch for the URL
"""

from __future__ import annotations

import json
import warnings
from functools import lru_cache
from pathlib import Path

from montin.utils.resource_loader import get_static


def vendor_dir() -> Path:
    """Folder holding the vendored libraries and their manifest."""
    return get_static("vendor")


@lru_cache(maxsize=1)
def load_manifest() -> dict:
    """Parsed ``manifest.json`` (cached)."""
    return json.loads((vendor_dir() / "manifest.json").read_text(encoding="utf-8"))


def _effective_version(plugin, entry: dict) -> str:
    return plugin.version or entry["version"]


def _vouchable(plugin, entry_version: str) -> bool:
    """Whether an SRI hash is valid for this plugin's resolved CDN URL.

    Only when the URL is the canonical one we hashed: no custom ``url`` and the
    default (vendored) version.
    """
    return plugin.url is None and (plugin.version in (None, entry_version))


def _js(mode: str, **kw) -> dict:
    return {"type": "js", "mode": mode, **kw}


def _css(mode: str, **kw) -> dict:
    return {"type": "css", "mode": mode, **kw}


def _file_asset(maker, mode_self_contained: bool, path: Path, filename: str) -> dict:
    """Bundled asset: inline when self-contained, else a copied sidecar file."""
    if mode_self_contained:
        return maker("inline", path=path)
    return maker("copy", path=path, filename=filename)


def resolve_plugin(plugin, *, source: str, self_contained: bool, sri: bool,
                   deck_theme: str | None = None) -> dict:
    """Resolve one plugin to ``{"name", "assets", "options"}``.

    Args:
        plugin: the declared :class:`Plugin` instance.
        source: the effective ``"cdn"`` or ``"bundled"`` (deck default / force
            already applied by the caller).
        self_contained: whether bundled assets are inlined (vs copied as sidecars).
        sri: whether to attach Subresource-Integrity hashes to CDN assets.
        deck_theme: the deck's theme name, used only to resolve Tabulator's
            ``theme="auto"`` to a concrete light/dark stylesheet.
    """
    name = plugin.name
    entry = load_manifest()[name]
    version = _effective_version(plugin, entry)
    lib_dir = vendor_dir() / name   # each library lives in its own subfolder
    assets: list[dict] = []
    options: dict = {}

    if source == "bundled" and plugin.version not in (None, entry["version"]):
        warnings.warn(
            f"Plugin {name!r}: bundled mode ships version {entry['version']}, "
            f"ignoring version={plugin.version!r}. Use source='cdn' for a custom "
            f"version.",
            stacklevel=2,
        )

    if name in ("plotly", "mermaid"):
        if source == "cdn":
            url = plugin.url or entry["cdn"].format(version=version)
            integrity = entry["sri"] if (sri and _vouchable(plugin, entry["version"])) else None
            assets.append(_js("src", url=url, integrity=integrity))
        else:
            assets.append(_file_asset(_js, self_contained, lib_dir / entry["js"], entry["js"]))
        if name == "mermaid":
            options["theme"] = getattr(plugin, "theme", "dark")

    elif name == "highlight":
        style = getattr(plugin, "style", entry["default_style"])
        if source == "cdn":
            css_url = entry["cdn_css"].format(version=version, style=style)
            css_integrity = entry["sri_css"].get(style) if (sri and _vouchable(plugin, entry["version"])) else None
            assets.append(_css("src", url=css_url, integrity=css_integrity))
            js_url = plugin.url or entry["cdn_js"].format(version=version)
            js_integrity = entry["sri_js"] if (sri and _vouchable(plugin, entry["version"])) else None
            assets.append(_js("src", url=js_url, integrity=js_integrity))
        else:
            if style not in entry["vendored_styles"]:
                warnings.warn(
                    f"Plugin 'highlight': style {style!r} is not vendored for "
                    f"bundled mode; using {entry['default_style']!r}. Vendored: "
                    f"{entry['vendored_styles']}.",
                    stacklevel=2,
                )
                style = entry["default_style"]
            css_file = entry["css_file"].format(style=style)
            assets.append(_file_asset(_css, self_contained, lib_dir / css_file, css_file))
            assets.append(_file_asset(_js, self_contained, lib_dir / entry["js"], entry["js"]))

    elif name == "mathjax":
        output = getattr(plugin, "output", entry["default_output"])
        if source == "cdn":
            url = plugin.url or entry["cdn"].format(version=version, output=output)
            integrity = entry["sri"].get(output) if (sri and _vouchable(plugin, entry["version"])) else None
            assets.append(_js("src", url=url, integrity=integrity))
        else:
            if output not in entry["vendored_outputs"]:
                warnings.warn(
                    f"Plugin 'mathjax': output {output!r} is not vendored for "
                    f"bundled mode; using {entry['default_output']!r}. Vendored: "
                    f"{entry['vendored_outputs']}. (Use source='cdn' for "
                    f"{output!r}.)",
                    stacklevel=2,
                )
                output = entry["default_output"]
            js_file = entry["js"].format(output=output)
            assets.append(_file_asset(_js, self_contained, lib_dir / js_file, js_file))
        options["output"] = output

    elif name == "tabulator":
        # montin-facing theme ("auto"/"light"/"dark") -> a vendored stylesheet.
        theme_key = getattr(plugin, "theme", "auto")
        if theme_key == "auto":
            theme_key = "light" if deck_theme == "light" else "dark"
        css_base = entry["theme_map"].get(theme_key) or entry["theme_map"][entry["default_theme"]]
        css_file = entry["css_file"].format(theme=css_base)
        if source == "cdn":
            css_url = entry["cdn_css"].format(version=version, theme=css_base)
            css_integrity = entry["sri_css"].get(css_base) if (sri and _vouchable(plugin, entry["version"])) else None
            assets.append(_css("src", url=css_url, integrity=css_integrity))
            js_url = plugin.url or entry["cdn_js"].format(version=version)
            js_integrity = entry["sri_js"] if (sri and _vouchable(plugin, entry["version"])) else None
            assets.append(_js("src", url=js_url, integrity=js_integrity))
        else:
            assets.append(_file_asset(_css, self_contained, lib_dir / css_file, css_file))
            assets.append(_file_asset(_js, self_contained, lib_dir / entry["js"], entry["js"]))

    else:  # pragma: no cover - guarded by Plugin subclasses
        raise KeyError(f"Unknown plugin {name!r}")

    return {"name": name, "assets": assets, "options": options}
