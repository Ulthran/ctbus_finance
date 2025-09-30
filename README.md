# ctbus_finance

Tools for importing real-world financial statements into [Beancount](https://beancount.github.io/) and exploring them with [Fava](https://beancount.github.io/fava/).

## Capital One credit card importer

`bean-extract ctbus_finance/importers/config.py csv/CapitalOneQuicksilver.csv > beancount/capitalone_quicksilver.beancount`

`python ctbus_finance/expense_accounts.py beancount/* > beancount/expense_accounts.beancount`

## Launching the Fava web UI

You can also launch the Fava web interface directly from Python using the provided helper:

```python
from ctbus_finance import launch_fava

# This will block while Fava is running.
launch_fava("~/Documents/finance.beancount", host="0.0.0.0", port=5000)
```

Pass ``open_browser=False`` to skip opening a browser window automatically, or supply additional CLI flags via ``extra_args``.
