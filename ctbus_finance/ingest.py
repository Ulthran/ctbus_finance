import csv
import pandas as pd
from ctbus_finance.db import get_session
from ctbus_finance.models import AccountHolding, CreditCardHolding
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Set, List


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


def ingest_csv(fp: Path, table: str, default_date: date | None = None):
    if default_date is None:
        default_date = datetime.today().date()

    session = get_session()

    if table == "account_holdings":
        holdings = load_account_holdings(fp, default_date)
        session.add_all(holdings)
        session.commit()

    elif table == "credit_card_holdings":
        holdings = load_credit_card_holdings(fp, default_date)
        session.add_all(holdings)
        session.commit()
    else:
        df = pd.read_csv(fp)
        if not df.empty:
            df.to_sql(table, con=session.bind, if_exists="append", index=False)
            session.commit()
        else:
            print(f"No new rows to insert into {table}")

    session.close()


def load_account_holdings(fp: Path, default_date: date) -> List[AccountHolding]:
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

    # Collect all price lookups that need to happen
    lookups: Dict[date, Set[str]] = {}
    for row in rows:
        if row["price"] is None and row["holding_id"]:
            lookups.setdefault(row["date"], set()).add(row["holding_id"])

        pd_val = row["purchase_date"]
        if pd_val and row["purchase_price"] is None:
            lookups.setdefault(pd_val, set()).add(row["holding_id"])

    # Download prices for the dates that need them
    # NOT IMPLEMENTED
    print(lookups)
    assert False

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
