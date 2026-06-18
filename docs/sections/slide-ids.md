# Slide IDs

Every slide has an identifier (`slide_id`). When `slide_id` is omitted, tessera
assigns an automatic one of the form `_slide-<n>` (the leading underscore
distinguishes it from user-supplied IDs). You can supply any hashable value —
integer, string, tuple, etc.

```python
# Auto-generated ID ("_slide-1")
slide = deck.add_slide("Introduction")
slide.add_text("Automatically managed ID.")

# Explicit integer ID
slide = deck.add_slide("Results", slide_id=1)
slide.add_text("example 2")

# Explicit string ID
slide = deck.add_slide("Details", ncols=2, slide_id="details")
slide.add_text("example 3.1")
```

## Overwriting slides

If a slide with the given `slide_id` already exists, it is **replaced in-place**
(same position in the deck). This is particularly useful in Jupyter notebooks:
re-running a cell recreates only that slide without duplicating it.

```python
# Re-running this cell overwrites the slide at id=1, preserving deck order
slide = deck.add_slide("Results", slide_id=1)
slide.add_text("Updated content.")
```

The screen recording below show how to use ids to help updating content.

![VSCode-workflow](../_static/img/live-editing/animation.webp)

### Title, section, and TOC slides

The structural slide methods take the same kind of stable identifier, so their
cells can be re-run without piling up duplicates:

```python
deck.add_title("Report",   title_id="cover")
deck.add_toc(               toc_id="toc")
deck.add_section("Methods", section_id="methods")
```

Re-running an `add_section(..., section_id=...)` cell also updates its entry in
the table of contents in place — it won't add a second TOC row.


## Retrieving and editing slides

Use `get_slide()` to fetch a slide by ID and continue adding cells to it from a
different notebook cell.

```python
slide = deck.get_slide("details")
slide.add_text("example 3.2")
```

Cell IDs work the same way within a slide: if a cell with `cell_id` already
exists, it is replaced.

```python
slide.add_text("first version",  cell_id=1)
slide.add_text("second version", cell_id=1)   # overwrites the first
```

## Removing slides

```python
deck.remove_slide("_slide-1")   # auto-generated ID
deck.remove_slide(1)            # explicit integer ID
```
