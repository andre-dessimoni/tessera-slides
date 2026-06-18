# API Reference

## Deck — `Deck`

```{eval-rst}
.. autoclass:: tessera.Deck
   :members: add_title, add_section, add_toc, add_slide, write
   :undoc-members: False
```

---

## Configuration

```{eval-rst}
.. autoclass:: tessera.Plugin
   :members:

.. autoclass:: tessera.SlideDefaults
   :members:

.. autoclass:: tessera.CellDefaults
   :members:
```

---

## Slide

```{eval-rst}
.. autoclass:: tessera.core.slide.Slide
   :members:
   :undoc-members: False
```

---

## Cells

```{eval-rst}
.. autoclass:: tessera.cells.text.TextCell
.. autoclass:: tessera.cells.misc.MetricCell
.. autoclass:: tessera.cells.table.TableCell
.. autoclass:: tessera.cells.image.ImageCell
.. autoclass:: tessera.cells.image_slider.ImageSliderCell
.. autoclass:: tessera.cells.misc.ListCell
.. autoclass:: tessera.cells.misc.CodeCell
.. autoclass:: tessera.cells.plotly.PlotlyCell
.. autoclass:: tessera.cells.misc.MermaidCell
.. autoclass:: tessera.cells.misc.HtmlCell
.. autoclass:: tessera.cells.misc.IframeCell
.. autoclass:: tessera.cells.misc.EmptyCell
```

---

## Exceptions

```{eval-rst}
.. autoclass:: tessera.HtmlSlidesError
.. autoclass:: tessera.CellPlacementError
.. autoclass:: tessera.PluginNotDeclaredError
.. autoclass:: tessera.ThemeNotFoundError
.. autoclass:: tessera.InvalidDataError
```
