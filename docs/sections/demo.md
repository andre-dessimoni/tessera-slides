# Live demo

The presentaion below is an example of the capabilities of téssera.

For better visualization click on the **Full screen** button on the bottom toolbar

Use the arrow keys or click the side arrows to navigate between slides.

The code used to generate it is shown in the sequence.

---

```{raw} html
<div style="
  width: 65vw;
  position: relative;
  padding: 0 1rem;
  box-sizing: border-box;
">
  <iframe
    src="../_static/example1.html"
    style="
      display: block;
      width: 100%;
      height: 600px;
      border: 1px solid var(--color-background-border, #ccc);
      border-radius: 8px;
    "
    loading="lazy"
    allowfullscreen
  ></iframe>
</div>
```

---

The code that generated this presentation:

```{literalinclude} ../examples/example1/example1.py
:language: python
```
