# ctbus_finance

A simple finance tracker using Python, SQLite, and Yahoo Finance

## Usage

Make CSVs for your accounts (name,type,institution), holdings (symbol,name,asset_type), and credit_cards (name,institution,card_type). See examples in `example_data/`. Sample datasets are provided there for testing. Then run:

```
ctbus_finance create_db
ctbus_finance ingest_csv accounts.csv accounts
ctbus_finance ingest_csv holdings.csv holdings
ctbus_finance ingest_csv credit_cards.csv credit_cards
```

You can add more later by adding to the CSVs and then rerunning the above (it won't add duplicates). Then each month, make CSVs for account_holdings (account_id,holding_id,quantity,price,purchase_date,purchase_price,percentage_cash,percentage_bond,percentage_large_cap,percentage_mid_cap,percentage_small_cap,percentage_international,percentage_other,notes) and credit_card_holdings (credit_card_id,balance,rewards). Then run:

```
ctbus_finance ingest_csv account_holdings_YYYY_MM_DD.csv account_holdings
ctbus_finance ingest_csv credit_card_holdings_YYYY_MM_DD.csv credit_card_holdings
ctbus_finance ingest_csv capitalone_transactions.csv capitalone_transactions
```

Use the optional `--date` argument to apply a specific date to all rows when your CSV doesn't include one:

```
ctbus_finance ingest_csv account_holdings_2024_01_01.csv account_holdings --date 2024-01-01
```

Note that it will fill in today's date for `date` unless it is specified in the CSV or provided via the `--date` option. It will also try to fill purchase_price for each asset from previous entries (especially useful if you have things Yahoo finance can't identify, so it won't keep looking that up and failing).

CapitalOne statement CSVs can also be imported using:

```
ctbus_finance ingest_csv capitalone_transactions.csv capitalone_transactions
```

Debit amounts are stored as negative values and credits as positive. Duplicate rows are ignored via a unique constraint.

Yahoo Finance imposes strict rate limits and the `yfinance` library does not provide a supported way to raise them. This project caches results and retries requests when possible, but bulk lookups may still exceed the limit.

### Web interface

Run the Flask application on `0.0.0.0` so the development server is reachable
outside the container:

```
flask --app ctbus_finance/flask_app run --host 0.0.0.0
```

Then open port `5000` in your browser.

## Dev

### Database migration

After making updates to the database models, you can update your schema using alembic:

```
alembic init alembic
(Go into alembic.ini and modify sqlalchemy.url to point to your database)
(Go into alembic/env.py and replace `target_metadata = None` with `from ctbus_finance import models` and `target_metadata = models.Base.metadata`)
alembic -c alembic.ini revision --autogenerate -m "Description of changes"
(Review script in alembic/versions/new_script_name.py)
alembic upgrade head
```