from ctbus_finance.db import get_session
from ctbus_finance.models import Holding
from datetime import datetime
from sqlalchemy.orm import Session


def create_holding(symbol: str, asset_type: str, name: str, session: Session = None):
    if not session:
        session = get_session()

    session.add(
        Holding(
            symbol=symbol,
            asset_type=asset_type,
            name=name,
        )
    )
    session.commit()
    session.close()
