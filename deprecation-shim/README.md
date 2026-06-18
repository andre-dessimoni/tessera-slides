# tessera-slides → renamed to **tessera-report**

This package has been **renamed**. `tessera-slides` is now a thin shim that just
installs [`tessera-report`](https://pypi.org/project/tessera-report/).

```bash
pip install tessera-report
```

Your code does not change — the import name was always `tessera`:

```python
from tessera import Deck   # was: from tessera import HTMLSlides
```

> Note: the main class `HTMLSlides` was renamed to `Deck` in the move to
> `tessera-report` 0.4.0. See the
> [changelog](https://tessera-report.readthedocs.io/).

Documentation: https://tessera-report.readthedocs.io/
Source: https://github.com/andre-dessimoni/tessera-report
