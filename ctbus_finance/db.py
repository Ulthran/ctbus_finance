import os
from datetime import datetime, date
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from ctbus_finance.models import Base


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
