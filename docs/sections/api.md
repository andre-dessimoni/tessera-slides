# API Reference

## Deck — `Deck`

```{eval-rst}
.. autoclass:: montin.Deck
   :members: add_title, add_section, add_toc, add_slide, write
   :undoc-members: False
```

---

## Configuration

```{eval-rst}
.. autoclass:: montin.SlideDefaults
   :members:

.. autoclass:: montin.CellDefaults
   :members:
```

---

## Plugins

```{eval-rst}
.. autoclass:: montin.Plugin
   :members:

.. autoclass:: montin.Plotly
.. autoclass:: montin.Mermaid
.. autoclass:: montin.Highlight
.. autoclass:: montin.MathJax
.. autoclass:: montin.Tabulator
```

---

## Security

```{eval-rst}
.. autoclass:: montin.Security
   :members:
```

---

## Slide

```{eval-rst}
.. autoclass:: montin.core.slide.Slide
   :members:
   :undoc-members: False
```

---

## Cells

```{eval-rst}
.. autoclass:: montin.cells.text.TextCell
.. autoclass:: montin.cells.misc.MetricCell
.. autoclass:: montin.cells.table.TableCell
.. autoclass:: montin.cells.image.ImageCell
.. autoclass:: montin.cells.image_slider.ImageSliderCell
.. autoclass:: montin.cells.misc.ListCell
.. autoclass:: montin.cells.misc.CodeCell
.. autoclass:: montin.cells.plotly.PlotlyCell
.. autoclass:: montin.cells.misc.MermaidCell
.. autoclass:: montin.cells.misc.HtmlCell
.. autoclass:: montin.cells.misc.IframeCell
.. autoclass:: montin.cells.misc.EmptyCell
```

---

## Exceptions

```{eval-rst}
.. autoclass:: montin.MontinError
.. autoclass:: montin.CellPlacementError
.. autoclass:: montin.PluginNotDeclaredError
.. autoclass:: montin.ThemeNotFoundError
.. autoclass:: montin.InvalidDataError
.. autoclass:: montin.SecurityError
```
