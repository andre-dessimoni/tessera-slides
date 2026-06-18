"""Deprecated shim — this project was renamed to ``tessera-report``.

You installed the old distribution name ``tessera-slides``. It now only depends
on ``tessera-report`` so existing installs keep working. Nothing here needs to
be imported: ``import tessera`` is unchanged and is provided by
``tessera-report``.

This module exists solely to emit a deprecation notice for anyone who imports
the old name directly.
"""

import warnings

warnings.warn(
    "The 'tessera-slides' distribution has been renamed to 'tessera-report'. "
    "Switch your dependency to 'tessera-report' (run "
    "`pip install tessera-report`). Your code does not change — "
    "'import tessera' and 'from tessera import Deck' work as before.",
    DeprecationWarning,
    stacklevel=2,
)

# Convenience re-export so `from tessera_slides import Deck` also works.
from tessera import *  # noqa: E402,F401,F403
