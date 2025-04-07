from ctbus_finance.db import get_session
from ctbus_finance.models import (
    Account,
    AccountHolding,
    CreditCard,
    CreditCardHolding,
    Holding,
)
from datetime import datetime
from sqlalchemy import extract
from sqlalchemy.orm import Session


def get_accounts() -> list[tuple[str, str, str, float]]:
    """
    Get a list of accounts from the database.

    Returns:
    List[tuple]: A list of tuples containing account information (Account Name, Type, Institution, and Total Value).
    """
    session = get_session()
    accounts = session.query(Account).all()
    current_month = datetime.now().month
    current_year = datetime.now().year
    account_holdings = (
        session.query(AccountHolding)
        .filter(
            extract("year", AccountHolding.date) == current_year,
            extract("month", AccountHolding.date) == current_month,
        )
        .all()
    )
    accounts = [
        (
            a.name,
            a.type,
            a.institution,
            round(
                sum(
                    [
                        ah.total_value
                        for ah in account_holdings
                        if ah.account_id == a.name
                    ]
                ),
                2,
            ),
        )
        for a in accounts
    ]
    session.close()
    return accounts


def get_credit_cards() -> list[tuple[str, str, str, float]]:
    """
    Get a list of credit cards from the database.

    Returns:
    List[tuple]: A list of tuples containing credit card information (Credit Card Name, Type, Institution, and Balance).
    """
    session = get_session()
    credit_cards = session.query(CreditCard).all()
    current_month = datetime.now().month
    current_year = datetime.now().year
    credit_card_holdings = (
        session.query(CreditCardHolding)
        .filter(
            extract("year", CreditCardHolding.date) == current_year,
            extract("month", CreditCardHolding.date) == current_month,
        )
        .all()
    )
    credit_cards = [
        (
            cc.name,
            cc.card_type,
            cc.institution,
            round(
                sum(
                    [
                        cch.balance
                        for cch in credit_card_holdings
                        if cch.credit_card_id == cc.name
                    ]
                ),
                2,
            ),
        )
        for cc in credit_cards
    ]
    session.close()
    return credit_cards


def get_net_value() -> float:
    """
    Get the net value of all accounts.

    Returns:
    float: The total net value of all accounts.
    """
    accounts = get_accounts()
    credit_cards = get_credit_cards()
    return round(
        sum([account[3] for account in accounts]) - sum([cc[3] for cc in credit_cards]),
        2,
    )


if __name__ == "__main__":
    print(get_accounts())
    print(get_credit_cards())
    print(get_net_value())
