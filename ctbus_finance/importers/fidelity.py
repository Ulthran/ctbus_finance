import csv
import datetime
import re
import titlecase
from beancount.core import amount, data, flags, number as beancount_number, position
from beancount.ingest import importer


_COLUMN_DATE = "Run Date"
_COLUMN_ACCOUNT_NAME = "Account"
_COLUMN_ACCOUNT_NO = "Account Number"
_COLUMN_ACTION = "Action"
_COLUMN_SYMBOL = "Symbol"
_COLUMN_DESCRIPTION = "Description"
_COLUMN_TYPE = "Type"
_COLUMN_EXCHANGE_QUANTITY = "Exchange Quantity"
_COLUMN_EXCHANGE_CURRENCY = "Exchange Currency"
_COLUMN_QUANTITY = "Quantity"
_COLUMN_CURRENCY = "Currency"
_COLUMN_PRICE = "Price"
_COLUMN_EXCHANGE_RATE = "Exchange Rate"
_COLUMN_COMMISSION = "Commission"
_COLUMN_FEES = "Fees"
_COLUMN_ACCRUED_INTEREST = "Accrued Interest"
_COLUMN_AMOUNT = "Amount"
_COLUMN_SETTLEMENT_DATE = "Settlement Date"


class Importer(importer.ImporterProtocol):
    def __init__(
        self,
        account: str,
        account_nos: dict[str, str],
        currency: str = "USD",
        account_patterns=None,
    ):
        self._account = account
        self._account_nos = account_nos
        self._currency = currency
        self._account_patterns = []
        if account_patterns:
            for pattern, account_name in account_patterns:
                self._account_patterns.append(
                    (re.compile(pattern, flags=re.IGNORECASE), account_name)
                )

    def _parse_amount(self, amount_raw):
        return amount.Amount(beancount_number.D(amount_raw), self._currency)

    def file_date(self, file):
        return max(map(lambda x: x.date, self.extract(file)))

    def file_account(self, _):
        return self._account

    def identify(self, file):
        with open(file.name, encoding="utf-8") as csv_file:
            # Skip first 2 lines before header
            next(csv_file)
            next(csv_file)
            for row in csv.DictReader(csv_file):
                return (
                    str(row[_COLUMN_ACCOUNT_NO]).strip('"') in self._account_nos.keys()
                )

    def extract(self, f):
        transactions = []

        with open(f.name, encoding="utf-8") as csv_file:
            # Skip first 2 lines before header
            next(csv_file)
            next(csv_file)
            for index, row in enumerate(csv.DictReader(csv_file)):
                metadata = data.new_metadata(f.name, index)
                transaction = self._extract_transaction_from_row(row, metadata)
                if not transaction:
                    continue
                transactions.append(transaction)

        return transactions

    def _extract_transaction_from_row(self, row, metadata):
        # Stop if this is a disclaimer row (no date, no account, etc.)
        if not row[_COLUMN_DATE] or not row[_COLUMN_ACCOUNT_NO]:
            return None

        # Parse date
        transaction_date = datetime.datetime.strptime(
            row[_COLUMN_DATE], "%m/%d/%Y"
        ).date()

        action = row[_COLUMN_ACTION].strip().upper()
        narration = titlecase.titlecase(row[_COLUMN_DESCRIPTION] or row[_COLUMN_ACTION])

        # Normalize amount
        raw_amt = row[_COLUMN_AMOUNT].replace("$", "").replace(",", "").strip()
        if not raw_amt:
            return None
        transaction_amount = self._parse_amount(raw_amt)

        if transaction_amount.number == 0:
            return None

        account_no = str(row[_COLUMN_ACCOUNT_NO]).strip('"')
        account = self._account_nos.get(account_no, self._account)

        symbol = row[_COLUMN_SYMBOL].strip()

        postings = []

        # --- Case 1: Dividend ---
        if "DIVIDEND RECEIVED" in action:
            postings = [
                data.Posting(
                    account=account + ":Cash",
                    units=transaction_amount,
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
                data.Posting(
                    account=f"Income:Dividends:{symbol}",
                    units=-transaction_amount,
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
            ]

        # --- Case 2: Deposit ---
        elif "CHECK RECEIVED" in action:
            postings = [
                data.Posting(
                    account=account + ":Cash",
                    units=transaction_amount,
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
                data.Posting(
                    account="TODO",  # figure out source account
                    units=-transaction_amount,
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
            ]

        # --- Case 3: Transfer ---
        elif "TRANSFERRED FROM" in action:
            postings = [
                data.Posting(
                    account=account + ":Cash",
                    units=transaction_amount,
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
                data.Posting(
                    account="TODO",  # figure out source account
                    units=-transaction_amount,
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
            ]

        # --- Case 4: Buy/Sell ---
        elif "BOUGHT" in action:
            symbol = row[_COLUMN_SYMBOL].strip()
            qty = beancount_number.D(row[_COLUMN_QUANTITY].replace(",", ""))
            cost_number = (transaction_amount.number / qty).quantize(
                beancount_number.D("0.0001")
            )
            cost = position.Cost(cost_number, self._currency, None, None)

            postings = [
                data.Posting(
                    account=account + ":" + symbol,
                    units=amount.Amount(qty, symbol),
                    cost=cost,
                    price=None,
                    flag=None,
                    meta=None,
                ),
                data.Posting(
                    account=account + ":Cash",
                    units=-transaction_amount,
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
            ]

        elif "SOLD" in action:
            symbol = row[_COLUMN_SYMBOL].strip()
            qty = beancount_number.D(row[_COLUMN_QUANTITY].replace(",", ""))

            postings = [
                data.Posting(
                    account=account + ":Cash",
                    units=transaction_amount,
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
                data.Posting(
                    account=account + ":" + symbol,
                    units=amount.Amount(-qty, symbol),
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
                data.Posting(
                    account="Income:CapitalGains",
                    units=-transaction_amount,  # placeholder, refine later
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
            ]

        else:
            # Skip unknown types for now
            return None

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
