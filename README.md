# ctbus_finance

A lightweight library for parsing monthly PDF statements from various financial
institutions.  Each provider has its own report subclass for applying provider
specific parsing logic.

## Usage

```python
from ctbus_finance import FidelityReport

report = FidelityReport("statement.pdf")
text = report.parse()
print(text)
```

The base :class:`Report` extracts text from the PDF using ``PyPDF2``.  The
provider specific subclasses are simple wrappers that can be extended with
custom parsing logic as needed.
