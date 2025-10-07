import csv
import datetime
from beancount.core import amount
from beancount.core import data
from beancount.core import flags
from beancount.core import number as beancount_number
from beangulp import importer


_COLUMN_CAT = "Cat"
_COLUMN_ID = "ID"
_COLUMN_DATETIME = "Datetime"
_COLUMN_TYPE = "Type"
_COLUMN_STATUS = "Status"
_COLUMN_NOTE = "Note"
_COLUMN_FROM = "From"
_COLUMN_TO = "To"
_COLUMN_AMOUNT_TOTAL = "Amount (total)"


class Importer(importer.ImporterProtocol):
    def __init__(self, account, currency="USD"):
        self._account = account
        self._currency = currency

    def _parse_amount(self, amount_raw: str):
        # Strip $ and commas, handle leading +/-
        cleaned = amount_raw.replace("$", "").replace(",", "").strip()
        return amount.Amount(beancount_number.D(cleaned), self._currency)

    def file_date(self, file):
        return max(map(lambda x: x.date, self.extract(file)))

    def file_account(self, file: str) -> str:
        return self._account

    def identify(self, file: str) -> bool:
        try:
            with open(file, encoding="utf-8") as csv_file:
                header = csv_file.readline()
                return "Account Statement - (@CharlieBushman)" in header
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
            # Skip first 2 lines before header
            next(csv_file)
            next(csv_file)
            reader = csv.DictReader(csv_file)
            for index, row in enumerate(reader):
                metadata = data.new_metadata(file, index)
                transaction = self._extract_transaction_from_row(row, metadata)
                if transaction:
                    transactions.append(transaction)
        return transactions

    def _extract_transaction_from_row(self, row, metadata):
        # Skip empty or summary rows
        if not row[_COLUMN_ID]:
            return None

        # Parse date from ISO string
        transaction_date = datetime.datetime.fromisoformat(row[_COLUMN_DATETIME]).date()

        # Narration: From -> To
        charge = str(row[_COLUMN_TYPE]).upper() == "CHARGE"
        if charge:
            narration = f"{row[_COLUMN_TO]} -> {row[_COLUMN_FROM]}"
        else:
            narration = f"{row[_COLUMN_FROM]} -> {row[_COLUMN_TO]}"

        if str(row[_COLUMN_TYPE]).upper() == "STANDARD TRANSFER":
            return None

        # Amount (already signed)
        try:
            transaction_amount = self._parse_amount(row[_COLUMN_AMOUNT_TOTAL])
        except Exception:
            return None

        if transaction_amount.number == 0:
            return None

        cat = row[_COLUMN_CAT].strip()
        if not cat:
            cat = "TODO"

        postings = [
            data.Posting(
                account=self._account,
                units=transaction_amount,
                cost=None,
                price=None,
                flag=None,
                meta=None,
            ),
            # Second leg left blank for manual annotation
            data.Posting(
                account=cat,
                units=-transaction_amount,
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
            narration=narration,
            tags=data.EMPTY_SET,
            links=data.EMPTY_SET,
            postings=postings,
        )
