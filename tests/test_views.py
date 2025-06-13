import os
from datetime import date

from ctbus_finance.db import create_database, get_session
from ctbus_finance.models import (
    Account,
    Holding,
    AccountHolding,
    CreditCard,
    CreditCardHolding,
)
from ctbus_finance.views import get_monthly_summary


def setup_simple_db(tmp_path):
    path = tmp_path / "test.sqlite"
    os.environ["CTBUS_FINANCE_DB_URI"] = f"sqlite:///{path}"
    create_database()
    session = get_session()
    session.add(Account(name="A", type="brokerage", institution="x"))
    session.add(Holding(symbol="ETF", name="Mixed ETF", asset_type="ETF"))
    session.add(Holding(symbol="CASH", name="Cash", asset_type="Cash"))
    session.add(CreditCard(name="CC", institution="bank", card_type="visa"))
    session.commit()
    session.add(
        AccountHolding(
            account_id="A",
            holding_id="ETF",
            date=date(2024, 1, 1),
            purchase_date=None,
            quantity=10,
            price=100,
            percentage_cash=50,
        )
    )
    session.add(
        AccountHolding(
            account_id="A",
            holding_id="CASH",
            date=date(2024, 1, 1),
            purchase_date=None,
            quantity=100,
            price=1,
        )
    )
    session.add(
        CreditCardHolding(
            credit_card_id="CC",
            date=date(2024, 1, 1),
            balance=50,
            rewards=0,
        )
    )
    session.commit()
    session.close()


def setup_money_market_db(tmp_path):
    path = tmp_path / "mm.sqlite"
    os.environ["CTBUS_FINANCE_DB_URI"] = f"sqlite:///{path}"
    create_database()
    session = get_session()
    session.add(Account(name="A", type="brokerage", institution="x"))
    session.add(Holding(symbol="MMF", name="MM fund", asset_type="Money Market"))
    session.commit()
    session.add(
        AccountHolding(
            account_id="A",
            holding_id="MMF",
            date=date(2024, 1, 1),
            purchase_date=None,
            quantity=100,
            price=1,
        )
    )
    session.commit()
    session.close()


def test_monthly_summary_percentage_cash(tmp_path):
    setup_simple_db(tmp_path)
    summary = get_monthly_summary()
    assert summary == [("2024-01", 1050.0, 600.0, 50.0)]


def test_monthly_summary_money_market(tmp_path):
    setup_money_market_db(tmp_path)
    summary = get_monthly_summary()
    assert summary == [("2024-01", 100.0, 100.0, 0.0)]
