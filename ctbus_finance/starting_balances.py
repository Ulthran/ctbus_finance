from datetime import date, datetime
from beancount.core import amount, data, flags, position
from ctbus_finance.sensitive import starting_investments
from decimal import Decimal


def d(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


default_date = d("2000-01-01")

def starting_balances() -> data.Directives:
    return [
        data.Transaction(
            meta={"source": "manual", "note": "Starting balance"},
            date=default_date,
            flag=flags.FLAG_OKAY,
            payee=None,
            narration="Starting Balance",
            tags=data.EMPTY_SET,
            links=data.EMPTY_SET,
            postings=[
                *[data.Posting(
                    account=k,
                    units=amount.Amount(Decimal(str(v[0])), v[1]),
                    cost=position.Cost(Decimal(str(v[2])), "USD", default_date, None),
                    price=None,
                    flag=None,
                    meta=None,
                ) for k, v in starting_investments.items()],
                data.Posting(
                    account="Income:Opening-Balances",
                    units=-amount.Amount(Decimal(str(sum([v[0] * v[2] for k, v in starting_investments.items()]))).quantize(Decimal("0.01")), "USD"),
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                ),
            ]
        )
    ]