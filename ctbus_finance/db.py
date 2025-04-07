import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session
from ctbus_finance.models import Base, AccountHolding
from ctbus_finance.yahoo_finance import get_price, get_ticker_data


def get_db_url() -> str:
    try:
        os.environ["CTBUS_FINANCE_DB_URI"]
    except KeyError:
        raise KeyError("CTBUS_FINANCE_DB_URI environment variable not set")
    return os.environ["CTBUS_FINANCE_DB_URI"]


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


def ingest_csv(fp: Path, table: str):
    session = get_session()
    df = pd.read_csv(fp)

    if table == "account_holdings":
        df = process_account_holdings(df, session)
    if table == "credit_card_holdings":
        df = process_credit_card_holdings(df, session)

    df.to_sql(table, con=session.bind, if_exists="replace", index=False)
    session.commit()
    session.close()


def process_account_holdings(df: pd.DataFrame, session: Session) -> pd.DataFrame:
    print("Processing account holdings...")
    for index, row in df.iterrows():
        print(row["account_id"], row["holding_id"], row["purchase_date"])
        df.loc[index, "quantity"] = float(row["quantity"])
        if pd.isna(row["date"]):
            df.loc[index, "date"] = datetime.today()
        if pd.isna(row["price"]):
            ticker = get_ticker_data(row["holding_id"])
            df.loc[index, "price"] = get_price(ticker, df.loc[index, "date"])
            if pd.notna(row["purchase_date"]):
                df.loc[index, "purchase_date"] = datetime.strptime(row["purchase_date"], "%Y-%m-%d").date()
                # First try to access from previous entries in the db
                if res := session.scalars(select(AccountHolding.purchase_price).filter_by(holding_id=row["holding_id"], purchase_date=row["purchase_date"])).first():
                    df.loc[index, "purchase_price"] = float(res)
                # Then look it up
                else:
                    df.loc[index, "purchase_price"] = get_price(ticker, datetime.strptime(row["purchase_date"], "%Y-%m-%d"))

        df.loc[index, "date"] = df.loc[index, "date"].date()

    dates = df.pop("date")
    df.insert(0, "date", dates)
    print("Purchase date type:", df["purchase_date"].dtype)

    df["percentage_cash"] = df["percentage_cash"].fillna(0).apply(lambda x: float(x) if x != "" else 0)
    df["percentage_bond"] = df["percentage_bond"].fillna(0).apply(lambda x: float(x) if x != "" else 0)
    df["percentage_large_cap"] = df["percentage_large_cap"].fillna(0).apply(lambda x: float(x) if x != "" else 0)
    df["percentage_mid_cap"] = df["percentage_mid_cap"].fillna(0).apply(lambda x: float(x) if x != "" else 0)
    df["percentage_small_cap"] = df["percentage_small_cap"].fillna(0).apply(lambda x: float(x) if x != "" else 0)
    df["percentage_international"] = df["percentage_international"].fillna(0).apply(lambda x: float(x) if x != "" else 0)
    df["percentage_other"] = df["percentage_other"].fillna(0).apply(lambda x: float(x) if x != "" else 0)

    return df


def process_credit_card_holdings(df: pd.DataFrame, session: Session) -> pd.DataFrame:
    print("Processing credit card holdings...")
    for index, row in df.iterrows():
        print(row["credit_card_id"], row["balance"], row["rewards"])
        df.loc[index, "balance"] = float(row["balance"])
        df.loc[index, "date"] = datetime.today().date()

    return df