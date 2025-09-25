# ctbus_finance

Tools for importing real-world financial statements into [Beancount](https://beancount.github.io/) and exploring them with [Fava](https://beancount.github.io/fava/).

## Capital One credit card importer

This project re-exports the `CreditImporter` from [mtlynch/beancount-capitalone](https://github.com/mtlynch/beancount-capitalone) so it can be used from the `ctbus_finance` namespace.

```python
from ctbus_finance import CapitalOneCreditCardImporter

importer = CapitalOneCreditCardImporter(
    account="Liabilities:CreditCard:CapitalOne",
    lastfour="1234",
    account_patterns=[
        (r"coffee", "Expenses:Food:Coffee"),
        (r"train", "Expenses:Transport:Transit"),
    ],
)

entries = importer.extract(open("~/Downloads/CapitalOne2024.csv"))
for entry in entries:
    print(entry)
```

The importer reads CSV exports generated from Capital One credit card statements and produces Beancount transactions with per-payee account mapping support.

## Launching the Fava web UI

You can also launch the Fava web interface directly from Python using the provided helper:

```python
from ctbus_finance import launch_fava

# This will block while Fava is running.
launch_fava("~/Documents/finance.beancount", host="0.0.0.0", port=5000)
```

Pass ``open_browser=False`` to skip opening a browser window automatically, or supply additional CLI flags via ``extra_args``.
