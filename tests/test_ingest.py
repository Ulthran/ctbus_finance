import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ctbus_finance.db import create_database, get_session
from ctbus_finance.ingest import ingest_csv
from ctbus_finance import models

DATA_DIR = ROOT / "example_data"

CSV_TABLES = [
    ("accounts.csv", "accounts"),
    ("holdings.csv", "holdings"),
    ("credit_cards.csv", "credit_cards"),
    ("account_holdings_2024_01_01.csv", "account_holdings"),
    ("account_holdings_2024_02_01.csv", "account_holdings"),
    ("account_holdings_2024_03_01.csv", "account_holdings"),
    ("credit_card_holdings_2024_01_01.csv", "credit_card_holdings"),
    ("credit_card_holdings_2024_02_01.csv", "credit_card_holdings"),
    ("credit_card_holdings_2024_03_01.csv", "credit_card_holdings"),
]


@pytest.fixture()
def db_path(tmp_path):
    path = tmp_path / "test.sqlite"
    os.environ["CTBUS_FINANCE_DB_URI"] = f"sqlite:///{path}"
    create_database(os.environ["CTBUS_FINANCE_DB_URI"])
    return path


def test_ingest_example_data(db_path):
    for filename, table in CSV_TABLES:
        ingest_csv(DATA_DIR / filename, table)

    session = get_session(os.environ["CTBUS_FINANCE_DB_URI"])
    assert session.query(models.Account).count() == 3
    assert session.query(models.Holding).count() == 8
    assert session.query(models.AccountHolding).count() == 36
    assert session.query(models.CreditCard).count() == 2
    assert session.query(models.CreditCardHolding).count() == 6
    session.close()
