"""
montin.exceptions
==================
Public exception hierarchy for the package.
"""


class MontinError(Exception):
    """Base class for all Montin exceptions."""


class CellPlacementError(MontinError):
    """
    Raised when a cell cannot be placed on the canvas.

    Cases:
    - col or row out of range (< 1 or > nrows/ncols)
    - col + colspan - 1 > ncols  or  row + rowspan - 1 > nrows
    - position already occupied by another cell
    """


class PluginNotDeclaredError(MontinError):
    """
    Raised when a cell requires a plugin not declared in Deck.

    Example: add_code() without Plugins.Highlight() in the plugins list.
    """


class ThemeNotFoundError(MontinError):
    """
    Raised when the folder for the specified theme is not found.
    """


class InvalidDataError(MontinError):
    """
    Raised when the type or format of data passed to an add_* method
    is invalid or cannot be interpreted.

    Example: add_table() receives an unsupported type, or a malformed CSV string.
    """


class SecurityError(MontinError):
    """
    Raised when a Security(...) constraint cannot be satisfied.

    Cases:
    - block_external=True but a plugin was explicitly set to source="cdn"
    - block_external=True but the rendered report still contains an external
      (http/https) resource URL
    """
