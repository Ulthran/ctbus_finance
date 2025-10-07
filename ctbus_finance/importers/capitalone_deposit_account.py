import csv
import datetime
import os
import re
import titlecase
from beancount.core import amount
from beancount.core import data
from beancount.core import flags
from beancount.core import number as beancount_number
from beangulp import importer


_COLUMN_ACCOUNT_NO = "Account Number"
_COLUMN_DESCRIPTION = "Transaction Description"
_COLUMN_DATE = "Transaction Date"
_COLUMN_TYPE = "Transaction Type"
_COLUMN_AMOUNT = "Transaction Amount"
_COLUMN_BALANCE = "Balance"


class Importer(importer.ImporterProtocol):
    def __init__(self, account, account_no, currency="USD", account_patterns=None):
        self._account = account
        self._account_no = account_no
        self._currency = currency
        self._account_patterns = []
        if account_patterns:
            for pattern, account_name in account_patterns:
                self._account_patterns.append(
                    (re.compile(pattern, flags=re.IGNORECASE), account_name)
                )

    def _parse_amount(self, amount_raw):
        return amount.Amount(beancount_number.D(amount_raw), self._currency)

    def file_date(self, file: str):
        return max(map(lambda x: x.date, self.extract(file)))

    def file_account(self, file: str) -> str:
        return self._account

    def identify(self, file: str) -> bool:
        try:
            with open(file, encoding="utf-8") as csv_file:
                for row in csv.DictReader(csv_file):
                    return row[_COLUMN_ACCOUNT_NO] == self._account_no
        except Exception as e:
            pass
        return False

    def sort(self, entries: data.Directives, reverse: bool = False) -> None:
        pass

    def extract(
        self, file: str, existing_entries: data.Directives = []
    ) -> data.Directives:
        transactions = []

        with open(file, encoding="utf-8") as csv_file:
            for index, row in enumerate(csv.DictReader(csv_file)):
                metadata = data.new_metadata(file, index)
                transaction = self._extract_transaction_from_row(row, metadata)
                if not transaction:
                    continue
                transactions.append(transaction)

        return transactions

    def _extract_transaction_from_row(self, row, metadata):
        try:
            transaction_date = datetime.datetime.strptime(
                row[_COLUMN_DATE], "%m/%d/%y"
            ).date()
        except ValueError:
            try:
                transaction_date = datetime.datetime.strptime(
                    row[_COLUMN_DATE], "%m/%d/%Y"
                ).date()
            except ValueError as e:
                raise e

        transaction_description = titlecase.titlecase(row[_COLUMN_DESCRIPTION])

        # Don't double count credit card payments
        # We count them on the credit card side instead of here
        # because here we don't know what card the payment is going to
        if "CAPITAL ONE CRCARDPMT" in transaction_description.upper():
            return None

        # Don't double count internal transfers
        # Only count the checking side "Deposit from" transactions
        if "WITHDRAWAL TO 360 CHECKING" in transaction_description.upper():
            return None

        if str(row[_COLUMN_TYPE]).upper() == "DEBIT":
            transaction_amount = self._parse_amount(row[_COLUMN_AMOUNT])
        elif str(row[_COLUMN_TYPE]).upper() == "CREDIT":
            # Negate the credit column so that it has opposite sign from debits.
            negated_credit_amount = "-" + row[_COLUMN_AMOUNT]
            transaction_amount = self._parse_amount(negated_credit_amount)
        else:
            return None  # 0 dollar transaction

        if transaction_amount == amount.Amount(beancount_number.D(0), self._currency):
            return None

        postings = [
            data.Posting(
                account=self._account,
                units=-transaction_amount,
                cost=None,
                price=None,
                flag=None,
                meta=None,
            )
        ]
        for pattern, account_name in self._account_patterns:
            if pattern.search(transaction_description):
                postings.append(
                    data.Posting(
                        account=account_name,
                        units=transaction_amount,
                        cost=None,
                        price=None,
                        flag=None,
                        meta=None,
                    )
                )
                break

        # For some reason, pylint thinks data.Transactions is not callable.
        # pylint: disable=not-callable
        return data.Transaction(
            meta=metadata,
            date=transaction_date,
            flag=flags.FLAG_OKAY,
            payee=None,
            narration=transaction_description,
            tags=data.EMPTY_SET,
            links=data.EMPTY_SET,
            postings=postings,
        )
