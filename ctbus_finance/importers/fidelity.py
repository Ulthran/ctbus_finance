import csv
import datetime
import re
import titlecase
from beancount.core import amount, data, flags, number as beancount_number, position
from beangulp import importer
from ctbus_finance.importers.stock_action import BuyAction, CheckReceivedAction, DividendAction, DistributionAction, FeeAction, ForeignTaxAction, MergerAction, SellAction, StockAction, TransferAction


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
        cusip_map: dict[str, str] = {},
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
        self._cusip_map = cusip_map


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
    
    def identify(self, file: str) -> bool:
        try:
            with open(file, encoding="utf-8") as csv_file:
                # Skip first 2 lines before header
                next(csv_file)
                next(csv_file)
                for row in csv.DictReader(csv_file):
                    return (
                        str(row[_COLUMN_ACCOUNT_NO]).strip('"') in self._account_nos.keys()
                    )
        except Exception as e:
            pass
        return False

    def sort(self, entries: data.Directives, reverse: bool = False) -> None:
        pass

    def extract(self, file: str, existing_entries: list[data.Directive] = []) -> list[data.Directive]:
        transactions = []

        with open(file, encoding="utf-8") as csv_file:
            # Skip first 2 lines before header
            next(csv_file)
            next(csv_file)
            for index, row in enumerate(csv.DictReader(csv_file)):
                metadata = data.new_metadata(file, index)
                transaction = self._extract_transaction_from_row(row, metadata)
                if not transaction:
                    continue
                transactions.append(transaction)

        transactions = self._consolidate_merger_transactions(transactions)

        return transactions

    def _extract_transaction_from_row(self, row, metadata):
        # Stop if this is a disclaimer row (no date, no account, etc.)
        if not row[_COLUMN_DATE] or not row[_COLUMN_ACCOUNT_NO]:
            return None
        
        transaction_date = datetime.datetime.strptime(row[_COLUMN_DATE], "%m/%d/%Y")
        action = row[_COLUMN_ACTION].strip().upper()
        narration = titlecase.titlecase(row[_COLUMN_DESCRIPTION] or row[_COLUMN_ACTION])

        # Normalize amount (always quantized to cents)
        raw_amt = row[_COLUMN_AMOUNT].replace("$", "").replace(",", "").strip()
        if not raw_amt:
            return None
        transaction_amount = self._parse_amount(raw_amt)

        account_no = str(row[_COLUMN_ACCOUNT_NO]).strip('"')
        account = self._account_nos.get(account_no, self._account)

        symbol = row[_COLUMN_SYMBOL].strip()

        # If Symbol looks numeric (CUSIP), map it to a proper ticker
        if symbol in self._cusip_map:
            clean_symbol = self._cusip_map[symbol]
        else:
            # fallback: ensure it’s at least 2 characters and all caps
            clean_symbol = re.sub(r"\W+", "", symbol).upper()
            if len(clean_symbol) == 1:
                clean_symbol = f"TICKER-{clean_symbol}"

        if "BOUGHT" in action:
            action_type = BuyAction
            symbol = clean_symbol
        elif "SOLD" in action:
            action_type = SellAction
            symbol = clean_symbol
        elif "DIVIDEND RECEIVED" in action:
            action_type = DividendAction
            symbol = clean_symbol
        elif "CHECK RECEIVED" in action:
            action_type = CheckReceivedAction
        elif "TRANSFERRED FROM" in action:
            action_type = TransferAction
        elif "TRANSFERRED TO" in action:
            return None # Handled by other side of transfer
        elif "MERGER" in action:
            action_type = MergerAction
            symbol = clean_symbol
            metadata["fidelity_action"] = row[_COLUMN_DESCRIPTION]
            metadata["fidelity_action_type"] = "MERGER"
        elif "DISTRIBUTION" in action:
            action_type = DistributionAction
            symbol = clean_symbol
            metadata["fidelity_action"] = row[_COLUMN_DESCRIPTION]
            metadata["todo"] = "Attach cost basis (same as original purchase)"
            metadata["todo_type"] = "DISTRIBUTION"
        elif "FOREIGN TAX PAID" in action:
            action_type = ForeignTaxAction
            symbol = clean_symbol
        elif "ADVISORY FEE" in action:
            action_type = FeeAction
            symbol = clean_symbol
        elif "LONG-TERM CAP GAIN" in action:
            action_type = DistributionAction
            symbol = clean_symbol
            metadata["fidelity_action"] = row[_COLUMN_DESCRIPTION]
        elif "FEE CHARGED" in action:
            action_type = FeeAction
            symbol = clean_symbol
        elif "IN LIEU OF FRX SHARE" in action:
            action_type = DistributionAction
            symbol = clean_symbol
            metadata["fidelity_action"] = row[_COLUMN_DESCRIPTION]
        else:
            print("Unhandled action:", action)
            return None

        action = action_type(
            date=transaction_date,
            account=account,
            symbol=symbol,
            quantity=self._quantize_qty(
                beancount_number.D(row[_COLUMN_QUANTITY].replace(",", ""))
            ) if row[_COLUMN_QUANTITY] else beancount_number.D("0.000000"),
            currency=self._currency,
            price=self._quantize_cash(beancount_number.D(row[_COLUMN_PRICE].replace(",", ""))),
            fees=self._quantize_cash(beancount_number.D(row[_COLUMN_FEES].replace(",", ""))) if row[_COLUMN_FEES] else beancount_number.D("0.00"),
            amount=self._quantize_cost(beancount_number.D(row[_COLUMN_AMOUNT].replace(",", ""))),
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
    
    def _consolidate_merger_transactions(self, transactions: list[data.Transaction]) -> list[data.Directive]:
        consolidated = []
        skip_next = False

        for i in range(len(transactions)):
            if skip_next:
                skip_next = False
                continue

            current = transactions[i]

            if (
                i < len(transactions) - 1
                and isinstance(current, data.Transaction)
                and isinstance(transactions[i + 1], data.Transaction)
                and "MERGER" == current.meta.get("fidelity_action_type", "")
                and "MERGER" == transactions[i + 1].meta.get("fidelity_action_type", "")
                and current.date == transactions[i + 1].date
            ):
                next_txn = transactions[i + 1]
                # Merge postings from both transactions
                merged_postings = current.postings + next_txn.postings
                merged_narration = f"{current.narration} / {next_txn.narration}"
                merged_metadata = {**current.meta, **next_txn.meta}

                consolidated.append(
                    data.Transaction(
                        meta=merged_metadata,
                        date=current.date,
                        flag=current.flag,
                        payee=None,
                        narration=merged_narration,
                        tags=data.EMPTY_SET,
                        links=data.EMPTY_SET,
                        postings=merged_postings,
                    )
                )
                skip_next = True
            else:
                consolidated.append(current)

        return consolidated