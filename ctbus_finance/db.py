import os
import pandas as pd
from datetime import datetime, date
from pathlib import Path
from sqlalchemy import create_engine, select
from typing import Dict, Set
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session
from ctbus_finance.models import Base, AccountHolding, CreditCardHolding
from ctbus_finance.yahoo_finance import (
    get_price,
    get_ticker_data,
    get_prices_batch,
)


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
    df = pd.read_csv(fp)

    if table == "account_holdings":
        df = process_account_holdings(df, session, default_date)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["purchase_date"] = df["purchase_date"].apply(
            lambda x: pd.to_datetime(x).date() if pd.notna(x) and x != "" else None
        )
        # drop duplicates within the CSV itself
        df.drop_duplicates(
            subset=["account_id", "holding_id", "date", "purchase_date"], inplace=True
        )
        # filter out rows that already exist in the database
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

        df = df[
            ~df.apply(
                lambda row: (
                    row["account_id"],
                    row["holding_id"],
                    row["date"],
                    row["purchase_date"],
                )
                in existing_keys,
                axis=1,
            )
        ]

    if table == "credit_card_holdings":
        df = process_credit_card_holdings(df, session, default_date)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df.drop_duplicates(subset=["credit_card_id", "date"], inplace=True)
        existing_keys = {
            (r.credit_card_id, r.date)
            for r in session.execute(
                select(CreditCardHolding.credit_card_id, CreditCardHolding.date)
            )
        }
        df = df[
            ~df.apply(
                lambda row: (row["credit_card_id"], row["date"]) in existing_keys,
                axis=1,
            )
        ]

    if not df.empty:
        df.to_sql(table, con=session.bind, if_exists="append", index=False)
        session.commit()
    else:
        print(f"No new rows to insert into {table}")
    session.close()


def process_account_holdings(
    df: pd.DataFrame, session: Session, default_date: date
) -> pd.DataFrame:
    print("Processing account holdings...")
    if "date" not in df.columns:
        df["date"] = default_date
    # Determine which prices need to be looked up and batch those requests
    lookup_dates: Dict[str, Set[datetime]] = {}
    for _, row in df.iterrows():
        symbol = row["holding_id"]
        if pd.isna(row["price"]):
            date_val = pd.to_datetime(
                row["date"] if pd.notna(row["date"]) else default_date
            )
            lookup_dates.setdefault(symbol, set()).add(date_val)
            if pd.notna(row["purchase_date"]):
                lookup_dates[symbol].add(pd.to_datetime(row["purchase_date"]))

    for symbol, dates in lookup_dates.items():
        get_prices_batch(symbol, dates)

    for index, row in df.iterrows():
        print(row["account_id"], row["holding_id"], row["purchase_date"])
        df.at[index, "quantity"] = float(row["quantity"])
        if pd.isna(row["date"]):
            df.at[index, "date"] = default_date
        if pd.isna(row["price"]):
            ticker = get_ticker_data(row["holding_id"])
            df.at[index, "price"] = get_price(
                ticker, pd.to_datetime(df.at[index, "date"])
            )
            if pd.notna(row["purchase_date"]):
                df.at[index, "purchase_date"] = datetime.strptime(
                    row["purchase_date"], "%Y-%m-%d"
                ).date()
                if res := session.scalars(
                    select(AccountHolding.purchase_price)
                    .filter_by(
                        holding_id=row["holding_id"], purchase_date=row["purchase_date"]
                    )
                    .filter(AccountHolding.purchase_price.is_not(None))
                ).first():
                    df.at[index, "purchase_price"] = float(res)
                else:
                    df.at[index, "purchase_price"] = get_price(
                        ticker, pd.to_datetime(row["purchase_date"])
                    )
    dates = df.pop("date")
    df.insert(0, "date", dates)
    print("Purchase date type:", df["purchase_date"].dtype)

    df["percentage_cash"] = (
        df["percentage_cash"].fillna(0).apply(lambda x: float(x) if x != "" else 0)
    )
    df["percentage_bond"] = (
        df["percentage_bond"].fillna(0).apply(lambda x: float(x) if x != "" else 0)
    )
    df["percentage_large_cap"] = (
        df["percentage_large_cap"].fillna(0).apply(lambda x: float(x) if x != "" else 0)
    )
    df["percentage_mid_cap"] = (
        df["percentage_mid_cap"].fillna(0).apply(lambda x: float(x) if x != "" else 0)
    )
    df["percentage_small_cap"] = (
        df["percentage_small_cap"].fillna(0).apply(lambda x: float(x) if x != "" else 0)
    )
    df["percentage_international"] = (
        df["percentage_international"]
        .fillna(0)
        .apply(lambda x: float(x) if x != "" else 0)
    )
    df["percentage_other"] = (
        df["percentage_other"].fillna(0).apply(lambda x: float(x) if x != "" else 0)
    )

    return df


def process_credit_card_holdings(
    df: pd.DataFrame, session: Session, default_date: date
) -> pd.DataFrame:
    print("Processing credit card holdings...")
    for index, row in df.iterrows():
        print(row["credit_card_id"], row["balance"], row["rewards"])
        df.at[index, "balance"] = float(row["balance"])
        df.at[index, "date"] = default_date

    return df
