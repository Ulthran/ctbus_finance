from ctbus_finance.db import get_session
from ctbus_finance.models import Account
from sqlalchemy.orm import Session


def create_account(name: str, account_type: str, institution: str, session: Session = None):
    """
    Create a new account in the database.

    Parameters:
    name (str): The name of the account.
    account_type (str): The type of the account (e.g., "Brokerage", "Roth IRA").
    institution (str): The institution of the account (e.g., "Vanguard", "Fidelity").
    session (Session): The SQLAlchemy session to use for the database operation.

    Returns:
    pd.DataFrame: A DataFrame containing the account information.
    """
    if not session:
        # Define this here instead of as a default argument in order to avoid loading it ahead of time
        session = get_session()

    session.add(
        Account(
            name=name,
            account_type=account_type,
            institution=institution,
        )
    )
    session.commit()
    session.close()