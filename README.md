# ctbus_finance

Tools for importing real-world financial statements into [Beancount](https://beancount.github.io/).

The first supported importer targets the CSV statements that Capital One issues for
credit card accounts. It converts each row in the CSV into a fully balanced
Beancount transaction with helpful metadata such as the posted date, category and
card number.

## Capital One credit card importer

```python
from ctbus_finance import CapitalOneCreditCardImporter

importer = CapitalOneCreditCardImporter(
    "Liabilities:CreditCard:CapitalOne",
    payee_map={"Coffee Shop": "Expenses:Food:Coffee"},
    category_map={"travel": "Expenses:Transport:Transit"},
)

entries = importer.extract("~/Downloads/CapitalOne2024.csv")
for entry in entries:
    print(entry)
```

Each entry contains two postings: one to the configured credit card account and
another to an expense (or payment) account. Payees and categories can be mapped
to more specific accounts via ``payee_map`` and ``category_map``.
