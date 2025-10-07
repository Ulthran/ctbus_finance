import csv
from beancount.core import amount
from beancount.core import data
from beancount.core import flags
from beancount.core import number as beancount_number
from beangulp import importer
from datetime import datetime
from decimal import Decimal


_COLUMN_DATE = "Date"
_COLUMN_DESCRIPTION = "Transaction"
_COLUMN_BALANCE = "Cash Balance"
_COLUMN_ATTACHMENTS = "Attachments"
_COLUMN_AMOUNT = "Amount"


class Importer(importer.ImporterProtocol):
    def __init__(self, account, currency="USD"):
        self._account = account
        self._currency = currency

    def identify(self, file: str) -> bool:
        try:
            with open(file, encoding="utf-8") as csv_file:
                next(csv_file)  # Skip first line
                header = csv_file.readline()
                return "Date,Transaction,Amount,HSA Cash Balance,Attachments" in header
        except Exception as e:
            pass
        return False

    def sort(self, entries: data.Directives, reverse: bool = False) -> None:
        pass

    def extract(
        self, file: str, existing_entries: list[data.Directive] = []
    ) -> list[data.Directive]:
        transactions = []
        with open(file, encoding="utf-8") as csv_file:
            next(csv_file)  # Skip first line
            reader = csv.DictReader(csv_file)
            for index, row in enumerate(reader):
                metadata = data.new_metadata(file, index)
                transaction = self._extract_transaction_from_row(row, metadata)
                if transaction:
                    transactions.append(transaction)
        return transactions

    def _extract_transaction_from_row(self, row, metadata):
        # Skip empty or summary rows
        if not row[_COLUMN_DATE]:
            return None

        transaction_date = datetime.strptime(row[_COLUMN_DATE], "%m/%d/%Y").date()
        description = str(row[_COLUMN_DESCRIPTION]).strip()
        transaction_amount = abs(
            float(
                str(row[_COLUMN_AMOUNT])
                .replace("$", "")
                .replace(",", "")
                .replace("(", "")
                .replace(")", "")
                .strip()
            )
        )

        if "INVESTMENT ADMIN FEE" in description.upper():
            account_from = self._account + ":Cash"
            account_to = "Expenses:Bank:HealthEquity"
        elif "INTEREST" in description.upper():
            account_from = "Income:Interest:HealthEquity"
            account_to = self._account + ":Cash"
        elif "INVESTMENT:" in description.upper():
            symbol = description.split(":")[-1].strip()
            account_from = self._account + ":Cash"
            account_to = self._account + ":" + symbol
        elif "EMPLOYEE CONTRIBUTION" in description.upper():
            account_from = "Income:Salary:UPenn"
            account_to = self._account + ":Cash"
        elif "EMPLOYER CONTRIBUTION" in description.upper():
            account_from = "Income:HSA-Contribution:UPenn"
            account_to = self._account + ":Cash"
        else:
            print("UNHANDLED HealthEquity transaction:", description)
            return None

        postings = [
            data.Posting(
                account=account_from,
                units=-amount.Amount(
                    Decimal(transaction_amount).quantize(Decimal("0.01")),
                    self._currency,
                ),
                cost=None,
                price=None,
                flag=None,
                meta=None,
            ),
            data.Posting(
                account=account_to,
                units=amount.Amount(
                    Decimal(transaction_amount).quantize(Decimal("0.01")),
                    self._currency,
                ),
                cost=None,
                price=None,
                flag=None,
                meta=None,
            ),
        ]

        return data.Transaction(
            meta=metadata,
            date=transaction_date,
            flag=flags.FLAG_OKAY,
            payee=None,
            narration=description,
            tags=data.EMPTY_SET,
            links=data.EMPTY_SET,
            postings=postings,
        )
