"""Sphinx configuration for tessera documentation."""

import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_HERE = Path(__file__).parent
_STATIC_DIR = _HERE / "_static"

# Add project root to sys.path for autodoc
sys.path.insert(0, str(_ROOT))

# ---------------------------------------------------------------------------
# Slide generation hook — build the embedded _static/*.html previews
#
# These run LOCALLY on every `make.bat html` / `make.bat live` build and the
# resulting .html files are committed to the repo. On Read the Docs we skip
# generation entirely and serve the committed files, so RTD doesn't need the
# heavy plotting/data dependencies (plotly, pandas, matplotlib) or local assets.
# ---------------------------------------------------------------------------

# Each entry is a standalone script that writes one or more files into _static/.
_SLIDE_GENERATORS = [
    _HERE / "examples" / "example1"   / "example1.py",
    _HERE / "examples" / "quickstart" / "quickstart.py",
    _HERE / "examples" / "layout"     / "layout.py",
    _HERE / "examples" / "cell_types" / "cell_types.py",
    _HERE / "examples" / "structure"  / "structure.py",
]


def _generate_slides(app=None):
    if os.environ.get("READTHEDOCS"):
        print("tessera: skipping slide generation on Read the Docs "
              "(serving committed _static/*.html)")
        return

    _STATIC_DIR.mkdir(exist_ok=True)
    env = {**os.environ, "PYTHONPATH": str(_ROOT)}
    for script in _SLIDE_GENERATORS:
        if not script.exists():
            print(f"tessera: skip — generator not found: {script.name}")
            continue
        try:
            subprocess.run(
                [sys.executable, str(script)],
                cwd=str(script.parent),
                check=True,
                timeout=120,
                env=env,
            )
            print(f"tessera: generated slides from {script.name}")
        except Exception as exc:
            print(f"tessera: warning — {script.name} failed: {exc}")


def setup(app):
    app.connect("builder-inited", _generate_slides)


# Allow running this module directly to (re)generate the slides without a build:
#   python docs/conf.py        (used by `make.bat slides`)
if __name__ == "__main__":
    _generate_slides()

# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------

project   = "tessera"
copyright = "2026, André Rezende Dessimoni Carvalho"
author    = "André Rezende Dessimoni Carvalho"
release   = "0.1.0"

# ---------------------------------------------------------------------------
# Extensions
# ---------------------------------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",     # Google/NumPy docstring style
    "sphinx.ext.viewcode",     # [source] links
    "myst_parser",             # Markdown support
]

# ---------------------------------------------------------------------------
# Autodoc
# ---------------------------------------------------------------------------

autodoc_typehints         = "description"
autodoc_member_order      = "bysource"
autodoc_default_options   = {
    "members":         True,
    "undoc-members":   False,
    "show-inheritance": True,
}

napoleon_google_docstring  = True
napoleon_numpy_docstring   = False

# ---------------------------------------------------------------------------
# MyST
# ---------------------------------------------------------------------------

myst_enable_extensions = ["colon_fence", "deflist"]

# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

html_static_path = ["_static"]

pygments_style = "default"

html_theme = "furo"
html_title = "tessera"
html_logo  = "_static/tessera-logo.png"
html_theme_options = {
    "sidebar_hide_name":    False,
    "navigation_with_keys": True,
    "source_repository":    "https://github.com/andre-dessimoni/tessera-report/",
    "source_branch":        "main",
    "source_directory":     "docs/",
}

html_js_files  = ["github-edit-icon.js"]
html_css_files = ["embed.css"]

# ---------------------------------------------------------------------------
# Source
# ---------------------------------------------------------------------------

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
