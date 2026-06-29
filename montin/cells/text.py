"""montin.cells.text — TextCell"""

from __future__ import annotations
from typing import TYPE_CHECKING
from montin.cells.base import Cell, CellParams

if TYPE_CHECKING:
    import jinja2


def _render_markdown(text: str) -> str:
    """Convert markdown to HTML using markdown-it-py if available."""
    try:
        from markdown_it import MarkdownIt
        md = MarkdownIt("commonmark")
        return md.render(text)
    except ImportError:
        pass
    # Fallback: wrap plain text in <p> tags preserving line breaks
    import html as _html
    escaped = _html.escape(text)
    return "<p>" + escaped.replace("\n\n", "</p><p>").replace("\n", "<br>") + "</p>"


class TextCell(Cell):
    """Text with Markdown and LaTeX support (via MathJax)."""

    def __init__(self, content: str, params: CellParams, markdown: bool = True) -> None:
        super().__init__(params)
        self.content = content
        self.markdown = markdown
        self.rendered_html = _render_markdown(content) if markdown else content

    def render(self, env: "jinja2.Environment") -> str:
        return env.get_template("cell_text.html").render(cell=self)
    
    def __repr__(self) -> str:
        return (
            f"TextCell(ID={self.params.cell_id!r}, content={self.content!r})"
            f" at row={self.params.row}, col={self.params.col}"
        )
