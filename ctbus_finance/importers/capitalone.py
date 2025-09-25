"""Utilities for importing Capital One credit card statements into Beancount."""

from __future__ import annotations

import csv
import datetime as dt
from decimal import Decimal
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from beancount.core import data
from beancount.core.amount import Amount
from beancount.core.data import EMPTY_SET, Posting, Transaction
from beancount.core.flags import FLAG_OKAY
from beancount.core.number import D

__all__ = ["CapitalOneCreditCardImporter", "CapitalOneTransaction"]


@dataclass(frozen=True)
class CapitalOneTransaction:
    """Representation of a single transaction parsed from the CSV file."""

    transaction_date: dt.date
    posted_date: dt.date
    description: str
    category: str
    amount: Amount
    card_last4: str | None

    @classmethod
    def from_csv_row(cls, row: Mapping[str, str], *, currency: str) -> "CapitalOneTransaction":
        """Create a transaction from a Capital One CSV row.

        The CSV exported from Capital One contains *either* a ``Debit`` or a ``Credit``
        column value for each transaction. Debits represent purchases (which increase
        the card liability) while credits represent payments or refunds (which reduce
        the balance). The returned :class:`Amount` uses positive numbers for debits and
        negative numbers for credits.
        """

        try:
            transaction_date = dt.datetime.strptime(
                row["Transaction Date"].strip(), "%m/%d/%Y"
            ).date()
        except (KeyError, ValueError) as exc:  # pragma: no cover - defensive
            raise ValueError(f"Invalid transaction date: {row.get('Transaction Date')!r}") from exc

        try:
            posted_date = dt.datetime.strptime(row["Posted Date"].strip(), "%m/%d/%Y").date()
        except (KeyError, ValueError) as exc:
            raise ValueError(f"Invalid posted date: {row.get('Posted Date')!r}") from exc

        description = row.get("Description", "").strip()
        category = row.get("Category", "").strip()

        debit_raw = row.get("Debit", "").strip()
        credit_raw = row.get("Credit", "").strip()

        debit_amount = _parse_amount(debit_raw)
        credit_amount = _parse_amount(credit_raw)

        if debit_amount is not None and credit_amount is not None:
            raise ValueError(
                f"Row has both debit and credit values: {debit_raw!r}, {credit_raw!r}"
            )

        if debit_amount is not None:
            value = debit_amount
        elif credit_amount is not None:
            value = -credit_amount
        else:  # pragma: no cover - Capital One always has a number in one column.
            raise ValueError("Row is missing both debit and credit values")

        card_no = row.get("Card No.", "").strip()
        card_last4 = card_no[-4:] if card_no else None

        return cls(
            transaction_date=transaction_date,
            posted_date=posted_date,
            description=description,
            category=category,
            amount=Amount(value, currency),
            card_last4=card_last4,
        )


class CapitalOneCreditCardImporter:
    """Parse Capital One credit card CSV statements into Beancount entries."""

    def __init__(
        self,
        account: str,
        *,
        currency: str = "USD",
        default_charge_account: str = "Expenses:Unknown",
        default_payment_account: str = "Assets:Unknown",
        payee_map: Mapping[str, str] | None = None,
        category_map: Mapping[str, str] | None = None,
    ) -> None:
        """Create a new importer.

        Args:
            account: The Beancount account name for the Capital One credit card.
            currency: Currency for generated postings. Defaults to ``"USD"``.
            default_charge_account: Fallback account used for purchases.
            default_payment_account: Fallback account used for payments/refunds.
            payee_map: Optional case-insensitive mapping from payee descriptions to
                expense accounts.
            category_map: Optional case-insensitive mapping from Capital One
                categories to expense accounts.
        """

        self.account = account
        self.currency = currency
        self.default_charge_account = default_charge_account
        self.default_payment_account = default_payment_account
        self.payee_map = {k.casefold(): v for k, v in (payee_map or {}).items()}
        self.category_map = {k.casefold(): v for k, v in (category_map or {}).items()}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def identify(self, file_path: Path | str) -> bool:
        """Return ``True`` if the file appears to be a Capital One CSV export."""

        try:
            first_line = Path(file_path).read_text(encoding="utf-8-sig").splitlines()[0]
        except IndexError:  # pragma: no cover - empty files handled gracefully
            return False
        except OSError:  # pragma: no cover - propagate the error for callers
            raise

        lowercase_header = first_line.lower()
        return "transaction date" in lowercase_header and "posted date" in lowercase_header

    def extract(self, file_path: Path | str) -> list[Transaction]:
        """Parse *file_path* and return Beancount :class:`Transaction` entries."""

        entries: list[Transaction] = []
        for index, transaction in enumerate(self._parse_rows(file_path), start=2):
            meta = data.new_metadata(str(file_path), index)
            meta["posted"] = transaction.posted_date.isoformat()
            if transaction.category:
                meta["category"] = transaction.category
            if transaction.card_last4:
                meta["card_last4"] = transaction.card_last4

            payee = transaction.description or None
            narration = transaction.category or transaction.description

            card_posting = Posting(self.account, transaction.amount, None, None, None, None)
            counter_amount = Amount(
                -transaction.amount.number, transaction.amount.currency
            )
            counter_account = self._lookup_account(transaction, counter_amount.number)
            other_posting = Posting(counter_account, counter_amount, None, None, None, None)

            entries.append(
                Transaction(
                    meta,
                    transaction.transaction_date,
                    FLAG_OKAY,
                    payee,
                    narration or "Capital One transaction",
                    EMPTY_SET,
                    EMPTY_SET,
                    [card_posting, other_posting],
                )
            )

        return entries

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _parse_rows(self, file_path: Path | str) -> Iterable[CapitalOneTransaction]:
        with Path(file_path).open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            expected_fields = {
                "Transaction Date",
                "Posted Date",
                "Card No.",
                "Description",
                "Category",
                "Debit",
                "Credit",
            }
            fieldnames = set(reader.fieldnames or [])
            missing = expected_fields - fieldnames
            if missing:
                raise ValueError(
                    "CSV does not match expected Capital One format; missing columns: "
                    + ", ".join(sorted(missing))
                )

            for row in reader:
                if not any(row.values()):
                    continue
                yield CapitalOneTransaction.from_csv_row(row, currency=self.currency)

    def _lookup_account(
        self, transaction: CapitalOneTransaction, raw_amount: Decimal
    ) -> str:
        if raw_amount > 0:
            # Counter posting for payments/refunds uses the payment account.
            default_account = self.default_payment_account
        else:
            default_account = self.default_charge_account

        description_key = (transaction.description or "").casefold()
        if description_key and description_key in self.payee_map:
            return self.payee_map[description_key]

        category_key = (transaction.category or "").casefold()
        if category_key and category_key in self.category_map:
            return self.category_map[category_key]

        return default_account


def _parse_amount(value: str) -> Decimal | None:
    value = value.strip()
    if not value:
        return None

    normalized = value.replace("$", "").replace(",", "")
    try:
        return D(normalized)
    except Exception as exc:  # pragma: no cover - surfaces invalid exports
        raise ValueError(f"Invalid monetary amount: {value!r}") from exc
