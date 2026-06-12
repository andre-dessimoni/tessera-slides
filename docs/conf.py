"""Sphinx configuration for tessera documentation."""

import shutil
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_HERE = Path(__file__).parent
_STATIC_DIR = _HERE / "_static"

# Add project root to sys.path for autodoc
sys.path.insert(0, str(_ROOT))

# ---------------------------------------------------------------------------
# Demo build hook — generate the _static/example1.html slide
# ---------------------------------------------------------------------------

_EXAMPLE_DIR    = _HERE / "examples" / "example1"
_EXAMPLE_SCRIPT = _EXAMPLE_DIR / "example1.py"

def _generate_demo(app):
    import os
    _STATIC_DIR.mkdir(exist_ok=True)
    env = {**os.environ, "PYTHONPATH": str(_ROOT)}
    try:
        subprocess.run(
            [sys.executable, str(_EXAMPLE_SCRIPT)],
            cwd=str(_EXAMPLE_DIR),
            check=True,
            timeout=90,
            env=env,
        )
        print("tessera demo: example1.html written to docs/_static/")
    except subprocess.CalledProcessError as exc:
        print(f"tessera demo: warning — could not generate demo: {exc}")
    except Exception as exc:
        print(f"tessera demo: warning — could not generate demo: {exc}")


def setup(app):
    app.connect("builder-inited", _generate_demo)

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
    "source_repository":    "https://github.com/andre-dessimoni/tessera-slides/",
    "source_branch":        "main",
    "source_directory":     "docs/",
}

html_js_files = ["github-edit-icon.js"]

# ---------------------------------------------------------------------------
# Source
# ---------------------------------------------------------------------------

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
