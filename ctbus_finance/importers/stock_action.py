from abc import ABC, abstractmethod
from beancount.core import amount, data, flags, position
from datetime import datetime
from decimal import Decimal


class StockAction(ABC):
    def __init__(
        self,
        date: datetime,
        account: str,
        symbol: str,
        quantity: Decimal,
        currency: str,
        price: Decimal,
        fees: Decimal,
        amount: Decimal,
        transaction_type: str,
    ) -> None:
        self.date = date.date()
        self.account = account
        self.symbol = symbol
        self.shares_converted = quantity and quantity < 0
        self.shares_received = quantity and quantity > 0
        self.quantity = abs(quantity.quantize(Decimal("0.000001")))
        self.currency = currency
        self.price = abs(price.quantize(Decimal("0.01")))
        self.fees = abs(fees.quantize(Decimal("0.01")))
        self.amount = abs(amount.quantize(Decimal("0.01")))
        self.type = transaction_type

    @abstractmethod
    def get_postings(self) -> list[data.Posting]:
        raise NotImplementedError()


class BuyAction(StockAction):
    def get_postings(self) -> list[data.Posting]:
        if self.quantity == 0:
            return [
                data.Posting(
                    account=self.account + ":" + self.symbol,
                    units=amount.Amount(self.amount, self.symbol),
                    cost=position.CostSpec(
                        number_per=None,
                        number_total=None,
                        currency=None,
                        date=None,
                        label=None,
                        merge=False,
                    ),
                    price=None,
                    flag=None,
                    meta=None,
                ),
                data.Posting(
                    account=self.account + ":Cash",
                    units=-amount.Amount(self.amount, self.currency),
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
            ]
        return [
            data.Posting(
                account=self.account + ":" + self.symbol,
                units=amount.Amount(self.quantity, self.symbol),
                cost=position.Cost(
                    (self.amount / self.quantity).quantize(Decimal("0.000001")),
                    self.currency,
                    self.date,
                    None,
                ),
                price=None,
                flag=None,
                meta=None,
            ),
            data.Posting(
                account=self.account + ":Cash",
                units=-amount.Amount(self.amount, self.currency),
                cost=None,
                price=None,
                flag=None,
                meta=None,
            ),
        ]


class SellAction(StockAction):
    def get_postings(self) -> list[data.Posting]:
        if self.quantity == 0:
            return [
                data.Posting(
                    account=self.account + ":Cash",
                    units=amount.Amount(self.amount, self.currency),
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
                data.Posting(
                    account=self.account + ":" + self.symbol,
                    units=-amount.Amount(self.amount, self.symbol),
                    cost=position.CostSpec(
                        number_per=None,
                        number_total=None,
                        currency=None,
                        date=None,
                        label=None,
                        merge=False,
                    ),
                    price=None,
                    flag=None,
                    meta=None,
                ),
            ]
        postings = [
            data.Posting(
                account=self.account + ":Cash",
                units=amount.Amount(self.amount, self.currency),
                cost=None,
                price=None,
                flag=None,
                meta=None,
            ),
            data.Posting(
                account=self.account + ":" + self.symbol,
                units=-amount.Amount(self.quantity, self.symbol),
                cost=position.CostSpec(
                    number_per=None,
                    number_total=None,
                    currency=None,
                    date=None,
                    label=None,
                    merge=False,
                ),
                price=None,
                flag=None,
                meta=None,
            ),
        ]

        if float(self.fees) > 0.00:
            postings.append(
                data.Posting(
                    account="Expenses:Trading-Fees",
                    units=amount.Amount(self.fees, self.currency),
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
            )

        return postings + [
            data.Posting(
                account="Income:CapitalGains:Cash",
                units=None,
                cost=None,
                price=None,
                flag=None,
                meta=None,
            ),
        ]


class DividendAction(StockAction):
    def get_postings(self) -> list[data.Posting]:
        return [
            data.Posting(
                account=self.account + ":Cash",
                units=amount.Amount(self.amount, self.currency),
                cost=None,
                price=None,
                flag=None,
                meta=None,
            ),
            data.Posting(
                account="Income:Dividends:Cash",
                units=-amount.Amount(self.amount, self.currency),
                cost=None,
                price=None,
                flag=None,
                meta=None,
            ),
        ]


class CheckReceivedAction(StockAction):
    def get_postings(self) -> list[data.Posting]:
        return [
            data.Posting(
                account=self.account + ":Cash",
                units=amount.Amount(self.amount, self.currency),
                cost=None,
                price=None,
                flag=None,
                meta=None,
            ),
            data.Posting(
                account=self.symbol if self.symbol else "TODO",
                units=-amount.Amount(self.amount, self.currency),
                cost=None,
                price=None,
                flag=None,
                meta=None,
            ),
        ]


class TransferAction(StockAction):
    def get_postings(self) -> list[data.Posting]:
        return [
            data.Posting(
                account=self.account + ":Cash",
                units=amount.Amount(self.amount, self.currency),
                cost=None,
                price=None,
                flag=None,
                meta=None,
            ),
            data.Posting(
                account=self.symbol if self.symbol else "TODO",
                units=-amount.Amount(self.amount, self.currency),
                cost=None,
                price=None,
                flag=None,
                meta=None,
            ),
        ]


class MergerAction(StockAction):
    def get_postings(self) -> list[data.Posting]:
        # Shares converted in merger
        if self.shares_converted:
            return [
                data.Posting(
                    account=self.account + ":" + self.symbol,
                    units=-amount.Amount(self.quantity, self.symbol),
                    cost=position.CostSpec(
                        number_per=None,
                        number_total=self.amount,
                        currency="USD",
                        date=None,
                        label=None,
                        merge=False,
                    ),
                    price=None,
                    flag=None,
                    meta=None,
                )
            ]
        # Shares received in merger
        elif self.shares_received:
            return [
                data.Posting(
                    account=self.account + ":" + self.symbol,
                    units=amount.Amount(self.quantity, self.symbol),
                    cost=position.CostSpec(
                        number_per=None,
                        number_total=self.amount,
                        currency="USD",
                        date=None,
                        label=None,
                        merge=False,
                    ),
                    price=None,
                    flag=None,
                    meta=None,
                )
            ]
        # Cash in lieu of fractional shares
        elif float(self.amount) != 0.00 and self.symbol.upper() == "CASH":
            return [
                data.Posting(
                    account=self.account + ":Cash",
                    units=amount.Amount(self.amount, self.currency),
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
                data.Posting(
                    account="Income:CorporateActions:Cash",
                    units=-amount.Amount(self.amount, self.currency),
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
            ]
        else:
            print("UNKNOWN MERGER ACTION:", self.symbol, self.quantity, self.amount)
            return []


class DistributionAction(StockAction):
    def get_postings(self) -> list[data.Posting]:
        if self.type == "SHARES":
            return [
                data.Posting(
                    account=self.account + ":" + self.symbol,
                    units=amount.Amount(self.quantity, self.symbol),
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
                data.Posting(
                    account="Equity:StockSplit:" + self.symbol,
                    units=-amount.Amount(self.quantity, self.symbol),
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
            ]

        return [
            data.Posting(
                account=self.account + ":Cash",
                units=amount.Amount(self.amount, self.currency),
                cost=None,
                price=None,
                flag=None,
                meta=None,
            ),
            data.Posting(
                account="Income:CorporateActions:Cash",
                units=-amount.Amount(self.amount, self.currency),
                cost=None,
                price=None,
                flag=None,
                meta=None,
            ),
        ]


class FeeAction(StockAction):
    def get_postings(self) -> list[data.Posting]:
        return [
            data.Posting(
                account=self.account + ":Cash",
                units=-amount.Amount(self.amount, self.currency),
                cost=None,
                price=None,
                flag=None,
                meta=None,
            ),
            data.Posting(
                account="Expenses:Trading-Fees",
                units=amount.Amount(self.amount, self.currency),
                cost=None,
                price=None,
                flag=None,
                meta=None,
            ),
        ]


class ForeignTaxAction(StockAction):
    def get_postings(self) -> list[data.Posting]:
        return [
            data.Posting(
                account=self.account + ":Cash",
                units=-amount.Amount(self.amount, self.currency),
                cost=None,
                price=None,
                flag=None,
                meta=None,
            ),
            data.Posting(
                account="Income:Taxes:Foreign",
                units=amount.Amount(self.amount, self.currency),
                cost=None,
                price=None,
                flag=None,
                meta=None,
            ),
        ]
