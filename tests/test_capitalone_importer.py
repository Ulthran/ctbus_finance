from __future__ import annotations

import datetime as dt
from pathlib import Path
import sys

from beancount.core import amount
from beancount.core.number import D

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ctbus_finance.importers import CapitalOneCreditCardImporter


CSV_HEADER = "Transaction Date,Posted Date,Card No.,Description,Category,Debit,Credit\n"


def write_csv(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "capitalone.csv"
    path.write_text(CSV_HEADER + body, encoding="utf-8")
    return path


def test_extract_basic_transactions(tmp_path: Path) -> None:
    csv_body = """
01/05/2024,01/07/2024,XXXXXXXXXXXX1234,Coffee Shop,Food & Drink,5.25,
01/08/2024,01/09/2024,XXXXXXXXXXXX1234,Online Store,Shopping,12.10,
01/12/2024,01/12/2024,XXXXXXXXXXXX1234,PAYMENT THANK YOU,Payment,,150.00
""".strip()
    csv_file = write_csv(tmp_path, csv_body)

    importer = CapitalOneCreditCardImporter("Liabilities:CreditCard:CapitalOne")
    entries = importer.extract(csv_file)

    assert len(entries) == 3

    purchase = entries[0]
    assert purchase.date == dt.date(2024, 1, 5)
    assert purchase.payee == "Coffee Shop"
    assert purchase.postings[0].account == "Liabilities:CreditCard:CapitalOne"
    assert purchase.postings[0].units == amount.Amount(D("5.25"), "USD")
    assert purchase.postings[1].account == "Expenses:Unknown"
    assert purchase.postings[1].units == amount.Amount(D("-5.25"), "USD")

    payment = entries[-1]
    assert payment.postings[0].units == amount.Amount(D("-150.00"), "USD")
    assert payment.postings[1].account == "Assets:Unknown"
    assert payment.meta["posted"] == "2024-01-12"
    assert payment.meta["card_last4"] == "1234"


def test_extract_with_payee_and_category_mappings(tmp_path: Path) -> None:
    csv_body = """
01/05/2024,01/07/2024,XXXXXXXXXXXX1234,Coffee Shop,Food & Drink,5.25,
01/06/2024,01/07/2024,XXXXXXXXXXXX1234,Transit Authority,Travel,3.50,
""".strip()
    csv_file = write_csv(tmp_path, csv_body)

    importer = CapitalOneCreditCardImporter(
        "Liabilities:CreditCard:CapitalOne",
        payee_map={"Coffee Shop": "Expenses:Food:Coffee"},
        category_map={"travel": "Expenses:Transport:Transit"},
    )
    entries = importer.extract(csv_file)

    first, second = entries

    assert first.postings[1].account == "Expenses:Food:Coffee"
    assert second.postings[1].account == "Expenses:Transport:Transit"


def test_identify_rejects_unrelated_file(tmp_path: Path) -> None:
    unrelated = tmp_path / "other.csv"
    unrelated.write_text("Date,Description,Amount\n", encoding="utf-8")

    importer = CapitalOneCreditCardImporter("Liabilities:CreditCard:CapitalOne")
    assert not importer.identify(unrelated)


def test_identify_accepts_capital_one_csv(tmp_path: Path) -> None:
    csv_file = write_csv(tmp_path, "01/01/2024,01/01/2024,XXXX,Coffee,Food,1.00,\n")

    importer = CapitalOneCreditCardImporter("Liabilities:CreditCard:CapitalOne")
    assert importer.identify(csv_file)


def test_extract_raises_for_invalid_amount(tmp_path: Path) -> None:
    csv_body = """
01/05/2024,01/07/2024,XXXXXXXXXXXX1234,Coffee Shop,Food & Drink,not-a-number,
""".strip()
    csv_file = write_csv(tmp_path, csv_body)

    importer = CapitalOneCreditCardImporter("Liabilities:CreditCard:CapitalOne")

    try:
        importer.extract(csv_file)
    except ValueError as exc:
        assert "Invalid monetary amount" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected a ValueError to be raised")
