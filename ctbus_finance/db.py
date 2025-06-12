import os
import csv
import pandas as pd
from datetime import datetime, date
from pathlib import Path
from sqlalchemy import create_engine, select
from typing import Dict, Set, List
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session
from ctbus_finance.models import Base, AccountHolding, CreditCardHolding
from ctbus_finance.yahoo_finance import (
    get_price,
    download_prices_for_date,
    download_price,
)


def _parse_date(val: str | None, default: date | None = None) -> date | None:
    if val is None or val == "":
        return default
    return datetime.strptime(val, "%Y-%m-%d").date()


def _parse_float(val: str | None) -> float | None:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except Exception:
        return None


def get_db_url() -> str:
    cwd = Path.cwd()
    return os.environ.get(
        "CTBUS_FINANCE_DB_URI", f"sqlite:///{cwd.resolve() / 'db.sqlite'}"
    )


def create_database(database_url: str = get_db_url()):
    """
    Create the database tables that don't exist using the provided database URL.

    Parameters:
    database_url (str): The database URL.
    """
    engine = create_engine(database_url)
    Base.metadata.create_all(engine, checkfirst=True)


def get_connection(database_url: str = get_db_url()) -> Connection:
    """
    Get a connection to the database using the provided database URL.

    Parameters:
    database_url (str): The database URL.

    Returns:
    connection: The connection to the database.
    """
    engine = create_engine(database_url)
    connection = engine.connect()
    return connection


def get_session(database_url: str = get_db_url()) -> Session:
    """
    Get a session to the database using the provided database URL.

    Parameters:
    database_url (str): The database URL.

    Returns:
    session: The session to the database.
    """
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def ingest_csv(fp: Path, table: str, default_date: date | None = None):
    if default_date is None:
        default_date = datetime.today().date()

    session = get_session()

    if table == "account_holdings":
        holdings = load_account_holdings(fp, session, default_date)
        existing_keys = {
            (
                r.account_id,
                r.holding_id,
                r.date,
                r.purchase_date,
            )
            for r in session.execute(
                select(
                    AccountHolding.account_id,
                    AccountHolding.holding_id,
                    AccountHolding.date,
                    AccountHolding.purchase_date,
                )
            )
        }
        holdings = [
            h
            for h in holdings
            if (h.account_id, h.holding_id, h.date, h.purchase_date)
            not in existing_keys
        ]
        if holdings:
            session.add_all(holdings)
            session.commit()
        else:
            print("No new rows to insert into account_holdings")

    elif table == "credit_card_holdings":
        holdings = load_credit_card_holdings(fp, default_date)
        existing_keys = {
            (r.credit_card_id, r.date)
            for r in session.execute(
                select(CreditCardHolding.credit_card_id, CreditCardHolding.date)
            )
        }
        holdings = [
            h for h in holdings if (h.credit_card_id, h.date) not in existing_keys
        ]
        if holdings:
            session.add_all(holdings)
            session.commit()
        else:
            print("No new rows to insert into credit_card_holdings")
    else:
        df = pd.read_csv(fp)
        if not df.empty:
            df.to_sql(table, con=session.bind, if_exists="append", index=False)
            session.commit()
        else:
            print(f"No new rows to insert into {table}")

    session.close()


def load_account_holdings(fp: Path, session: Session, default_date: date) -> List[AccountHolding]:
    print("Processing account holdings...")
    with open(fp, newline="") as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]

    for row in rows:
        row["date"] = _parse_date(row.get("date"), default_date)
        row["purchase_date"] = _parse_date(row.get("purchase_date"))
        row["quantity"] = float(row.get("quantity") or 0)
        row["price"] = _parse_float(row.get("price"))
        row["purchase_price"] = _parse_float(row.get("purchase_price"))
        for field in [
            "percentage_cash",
            "percentage_bond",
            "percentage_large_cap",
            "percentage_mid_cap",
            "percentage_small_cap",
            "percentage_international",
            "percentage_other",
        ]:
            row[field] = float(row.get(field) or 0)

    # fetch missing current prices in batches
    lookups: Dict[date, Set[str]] = {}
    for row in rows:
        if row["price"] is None:
            lookups.setdefault(row["date"], set()).add(row["holding_id"])

    for d, symbols in lookups.items():
        prices = download_prices_for_date(symbols, d)
        for row in rows:
            if row["price"] is None and row["date"] == d and row["holding_id"] in prices:
                row["price"] = prices[row["holding_id"]]

    # fetch purchase prices individually
    for row in rows:
        pd_val = row["purchase_date"]
        if pd_val and row["purchase_price"] is None:
            res = session.scalars(
                select(AccountHolding.purchase_price)
                .filter_by(holding_id=row["holding_id"], purchase_date=pd_val)
                .filter(AccountHolding.purchase_price.is_not(None))
            ).first()
            if res is not None:
                row["purchase_price"] = float(res)
            else:
                row["purchase_price"] = download_price(row["holding_id"], pd_val)

    holdings: List[AccountHolding] = []
    for row in rows:
        holdings.append(
            AccountHolding(
                account_id=row["account_id"],
                holding_id=row["holding_id"],
                date=row["date"],
                purchase_date=row["purchase_date"],
                quantity=row["quantity"],
                price=row["price"],
                purchase_price=row["purchase_price"],
                percentage_cash=row.get("percentage_cash"),
                percentage_bond=row.get("percentage_bond"),
                percentage_large_cap=row.get("percentage_large_cap"),
                percentage_mid_cap=row.get("percentage_mid_cap"),
                percentage_small_cap=row.get("percentage_small_cap"),
                percentage_international=row.get("percentage_international"),
                percentage_other=row.get("percentage_other"),
                notes=row.get("notes"),
            )
        )

    return holdings


def load_credit_card_holdings(fp: Path, default_date: date) -> List[CreditCardHolding]:
    print("Processing credit card holdings...")
    with open(fp, newline="") as f:
        reader = csv.DictReader(f)
        holdings: List[CreditCardHolding] = []
        for row in reader:
            holdings.append(
                CreditCardHolding(
                    credit_card_id=row["credit_card_id"],
                    date=_parse_date(row.get("date"), default_date),
                    balance=float(row.get("balance") or 0),
                    rewards=_parse_float(row.get("rewards")),
                )
            )

    return holdings
