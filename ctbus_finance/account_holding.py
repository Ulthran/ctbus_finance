import pandas as pd
from ctbus_finance.db import get_session
from ctbus_finance.models import AccountHolding, Holding
from ctbus_finance.yahoo_finance import get_ticker_data, get_price
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime


def create_account_holding(
    account_id: int,
    holding_id: int,
    date: datetime = datetime.today(),
    quantity: float = 0.0,
    purchase_date: datetime = datetime.today(),
    session: Session = None,
):
    """
    Create a new account holding in the database.

    Parameters:
    account_id (int): The ID of the account.
    holding_id (int): The ID of the holding.
    date (datetime): The date of the holding.
    quantity (float): The quantity of the holding.
    purchase_date (datetime): The purchase date of the holding.
    session (Session): The SQLAlchemy session to use for the database operation.
    """
    if not session:
        session = get_session()

    yf_data = get_ticker_data(session.get(Holding, holding_id).symbol)
    price = get_price(yf_data, date)
    purchase_price = get_price(yf_data, purchase_date)
    if not price or not purchase_price:
        raise ValueError(
            f"Price data not available for ticker {session.get(Holding, holding_id).symbol} on date {date} or purchase date {purchase_date}"
        )

    session.add(
        AccountHolding(
            account_id=account_id,
            holding_id=holding_id,
            date=date,
            quantity=quantity,
            price=price,
            purchase_date=purchase_date,
            purchase_price=purchase_price,
        )
    )
    session.commit()
    session.close()
