# ctbus_finance

Tools for importing real-world financial statements into [Beancount](https://beancount.github.io/) and exploring them with [Fava](https://beancount.github.io/fava/).

I'll be the first to admit, everything here is messy. It's intended for personal use but if anyone comes away with useful ideas from it that's great!

## Setup

- Make `csv/` and `beancount/` dirs
- Download CSVs to `csv/`
- Make `ctbus_finance/sensitive.py` with appropriate values
- Make env `python -m venv env/` and activate `source env/bin/activate`
- Install `pip install -e .`

## Importing data

`python ctbus_finance/import.py`

Steps:

- Collect CSVs
- Import CSVs as Transacations
- Reconcile Transactions
- Collect commodities for pricing
- Collect price data

## Launching the Fava web UI

`python ctbus_finance/gui.py`