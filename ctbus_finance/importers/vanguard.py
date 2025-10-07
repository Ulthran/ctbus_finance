import csv
import datetime
import re
from typing import Type
import titlecase
from beancount.core import amount, data, flags, number as beancount_number, position
from beangulp import importer
from ctbus_finance.importers.stock_action import (
    BuyAction,
    CheckReceivedAction,
    DividendAction,
    DistributionAction,
    FeeAction,
    ForeignTaxAction,
    MergerAction,
    SellAction,
    StockAction,
    TransferAction,
)


_COLUMN_DATE = "Trade Date"
_COLUMN_ACCOUNT_NO = "Account Number"
_COLUMN_NAME = "Investment Name"
_COLUMN_ACTION = "Action"
_COLUMN_SYMBOL = "Symbol"
_COLUMN_DESCRIPTION = "Transaction Description"
_COLUMN_TYPE = "Transaction Type"
_COLUMN_QUANTITY = "Shares"
_COLUMN_PRINCIPAL_AMOUNT = "Principal Amount"
_COLUMN_PRICE = "Share Price"
_COLUMN_FEES = "Commissions and Fees"
_COLUMN_ACCRUED_INTEREST = "Accrued Interest"
_COLUMN_AMOUNT = "Net Amount"
_COLUMN_SETTLEMENT_DATE = "Settlement Date"
_Column_ACCOUNT_TYPE = "Account Type"


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

    # ----------------------------
    # Quantizers
    # ----------------------------
    def _quantize_cash(self, value):
        """Quantize to 2 decimals for USD cash amounts."""
        return value.quantize(beancount_number.D("0.01"))

    def _quantize_qty(self, value):
        """Quantize to 6 decimals for share quantities."""
        return value.quantize(beancount_number.D("0.000001"))

    def _quantize_cost(self, value):
        """Quantize to 6 decimals for per-share cost basis."""
        return value.quantize(beancount_number.D("0.000001"))

    def _parse_amount(self, amount_raw):
        num = beancount_number.D(amount_raw)
        return amount.Amount(self._quantize_cash(num), self._currency)

    def file_date(self, file):
        return max(map(lambda x: x.date, self.extract(file)))

    def file_account(self, file: str) -> str:
        return self._account

    def _header_lines(self, file: str) -> int:
        with open(file, encoding="utf-8") as csv_file:
            # Skip first header
            next(csv_file)
            line_count = 1
            while not next(csv_file).startswith("Account Number,"):
                line_count += 1
            return line_count

    def identify(self, file: str) -> bool:
        try:
            with open(file, encoding="utf-8") as csv_file:
                for _ in range(self._header_lines(file)):
                    next(csv_file)
                for row in csv.DictReader(csv_file):
                    return str(row[_COLUMN_ACCOUNT_NO]) in self._account_nos
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
            for _ in range(self._header_lines(file)):
                next(csv_file)
            for index, row in enumerate(csv.DictReader(csv_file)):
                metadata = data.new_metadata(file, index)
                transaction = self._extract_transaction_from_row(row, metadata)
                if not transaction:
                    continue
                transactions.append(transaction)

        return transactions

    def _extract_transaction_from_row(self, row, metadata):
        transaction_date = datetime.datetime.strptime(row[_COLUMN_DATE], "%Y-%m-%d")
        action_str = row[_COLUMN_TYPE].strip().upper()
        narration = titlecase.titlecase(row[_COLUMN_DESCRIPTION] or row[_COLUMN_ACTION])

        # Normalize amount (always quantized to cents)
        raw_amt = row[_COLUMN_AMOUNT].replace("$", "").replace(",", "").strip()
        if not raw_amt:
            return None
        transaction_amount = self._parse_amount(raw_amt)

        account_no = str(row[_COLUMN_ACCOUNT_NO])
        account = self._account_nos.get(account_no, self._account)

        symbol = row[_COLUMN_SYMBOL].strip()

        if action_str == "DIVIDEND":
            action_type = DividendAction
        elif action_str == "REINVESTMENT":
            action_type = BuyAction
        elif action_str == "BUY":
            action_type = BuyAction
        elif action_str == "SELL":
            action_type = SellAction
        elif action_str == "SWEEP IN":
            action_type = BuyAction
        elif action_str == "SWEEP OUT":
            action_type = SellAction
        elif action_str == "CONTRIBUTION":
            action_type = BuyAction
            symbol = "VMFXX"  # Sweep into money market fund
        else:
            print("Unhandled action:", action_str)
            return None

        action = action_type(
            date=transaction_date,
            account=account,
            symbol=symbol,
            quantity=(
                self._quantize_qty(
                    beancount_number.D(row[_COLUMN_QUANTITY].replace(",", ""))
                )
                if row[_COLUMN_QUANTITY]
                else beancount_number.D("0.000000")
            ),
            currency=self._currency,
            price=self._quantize_cash(
                beancount_number.D(row[_COLUMN_PRICE].replace(",", ""))
            ),
            fees=(
                self._quantize_cash(
                    beancount_number.D(row[_COLUMN_FEES].replace(",", ""))
                )
                if row[_COLUMN_FEES]
                else beancount_number.D("0.00")
            ),
            amount=self._quantize_cost(
                beancount_number.D(row[_COLUMN_AMOUNT].replace(",", ""))
            ),
            transaction_type=row[_COLUMN_TYPE].strip().upper(),
        )
        postings = action.get_postings()

        return data.Transaction(
            meta=metadata,
            date=transaction_date.date(),
            flag=flags.FLAG_OKAY,
            payee=None,
            narration=narration,
            tags=data.EMPTY_SET,
            links=data.EMPTY_SET,
            postings=postings,
        )
