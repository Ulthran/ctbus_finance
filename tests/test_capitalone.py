import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ctbus_finance.db import create_database, get_session
from ctbus_finance.ingest import ingest_csv
from ctbus_finance import models
from ctbus_finance.views import get_capitalone_category_totals

DATA_DIR = ROOT / "example_data"


def test_capitalone_ingest_and_totals(tmp_path):
    path = tmp_path / "capone.sqlite"
    os.environ["CTBUS_FINANCE_DB_URI"] = f"sqlite:///{path}"
    create_database()

    csv_path = DATA_DIR / "capitalone_transactions.csv"
    ingest_csv(csv_path, "capitalone_transactions")
    # repeat ingestion to ensure duplicates aren't added
    ingest_csv(csv_path, "capitalone_transactions")

    session = get_session()
    assert session.query(models.CapitalOneTransaction).count() == 4
    session.close()

    totals = dict(get_capitalone_category_totals())
    assert totals.get("Food and Drink") == -5.0
    assert totals.get("Income") == 1000.0
    assert totals.get("Groceries") == -30.0
