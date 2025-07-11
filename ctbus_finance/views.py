from ctbus_finance.db import get_session
from ctbus_finance.models import (
    Account,
    AccountHolding,
    CreditCard,
    CreditCardHolding,
    Holding,
)
from datetime import datetime
from sqlalchemy import extract, func, case
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


def get_monthly_net_worth() -> list[tuple[str, float]]:
    """Return net worth totals grouped by month."""
    session = get_session()
    account_sums = (
        session.query(
            extract("year", AccountHolding.date).label("year"),
            extract("month", AccountHolding.date).label("month"),
            func.sum(AccountHolding.quantity * AccountHolding.price).label("total"),
        )
        .group_by("year", "month")
        .all()
    )
    credit_sums = (
        session.query(
            extract("year", CreditCardHolding.date).label("year"),
            extract("month", CreditCardHolding.date).label("month"),
            func.sum(CreditCardHolding.balance).label("total"),
        )
        .group_by("year", "month")
        .all()
    )
    acc = {(int(y), int(m)): float(t or 0) for y, m, t in account_sums}
    cc = {(int(y), int(m)): float(t or 0) for y, m, t in credit_sums}
    all_months = sorted(set(acc.keys()) | set(cc.keys()))

    result: list[tuple[str, float]] = []
    for y, m in all_months:
        dt = datetime(int(y), int(m), 1)
        label = dt.strftime("%Y-%m")
        net = round(acc.get((y, m), 0.0) - cc.get((y, m), 0.0), 2)
        result.append((label, net))
    session.close()
    return result


def get_monthly_percentage_totals(
    column: str, session: Session | None = None
) -> dict[tuple[int, int], float]:
    """Return totals grouped by month based on a percentage column."""
    own_session = False
    if session is None:
        session = get_session()
        own_session = True

    percentage_col = getattr(AccountHolding, column)
    sums = (
        session.query(
            extract("year", AccountHolding.date).label("year"),
            extract("month", AccountHolding.date).label("month"),
            func.sum(
                AccountHolding.quantity
                * AccountHolding.price
                * func.coalesce(percentage_col, 0)
                / 100
            ).label("total"),
        )
        .group_by("year", "month")
        .all()
    )
    result = {(int(y), int(m)): float(t or 0) for y, m, t in sums}
    if own_session:
        session.close()
    return result


def get_monthly_asset_type_totals(
    asset_types: list[str], session: Session | None = None
) -> dict[tuple[int, int], float]:
    """Return totals grouped by month for given asset types."""
    own_session = False
    if session is None:
        session = get_session()
        own_session = True

    lower_types = [t.lower() for t in asset_types]
    sums = (
        session.query(
            extract("year", AccountHolding.date).label("year"),
            extract("month", AccountHolding.date).label("month"),
            func.sum(AccountHolding.quantity * AccountHolding.price).label("total"),
        )
        .join(Holding, AccountHolding.holding_id == Holding.symbol)
        .filter(func.lower(Holding.asset_type).in_(lower_types))
        .group_by("year", "month")
        .all()
    )
    result = {(int(y), int(m)): float(t or 0) for y, m, t in sums}
    if own_session:
        session.close()
    return result


def get_monthly_summary() -> list[tuple[str, float, float, float]]:
    """Return net worth, cash value, and credit card totals grouped by month."""
    session = get_session()

    account_sums = (
        session.query(
            extract("year", AccountHolding.date).label("year"),
            extract("month", AccountHolding.date).label("month"),
            func.sum(AccountHolding.quantity * AccountHolding.price).label("total"),
        )
        .group_by("year", "month")
        .all()
    )

    cash_dict = get_monthly_percentage_totals("percentage_cash", session)

    credit_sums = (
        session.query(
            extract("year", CreditCardHolding.date).label("year"),
            extract("month", CreditCardHolding.date).label("month"),
            func.sum(CreditCardHolding.balance).label("total"),
        )
        .group_by("year", "month")
        .all()
    )

    acc = {(int(y), int(m)): float(t or 0) for y, m, t in account_sums}
    cash = cash_dict
    cc = {(int(y), int(m)): float(t or 0) for y, m, t in credit_sums}
    all_months = sorted(set(acc.keys()) | set(cash.keys()) | set(cc.keys()))

    result: list[tuple[str, float, float, float]] = []
    for y, m in all_months:
        dt = datetime(int(y), int(m), 1)
        label = dt.strftime("%Y-%m")
        total_accounts = acc.get((y, m), 0.0)
        cash_val = cash.get((y, m), 0.0)
        credit_val = cc.get((y, m), 0.0)
        net = round(total_accounts - credit_val, 2)
        result.append((label, net, cash_val, credit_val))
    session.close()
    return result


if __name__ == "__main__":
    print(get_accounts())
    print(get_credit_cards())
    print(get_net_value())
    print(get_monthly_net_worth())
    print(get_monthly_summary())
