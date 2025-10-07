from beancount.core import amount, convert, data, inventory, position, realization
from collections import deque
from ctbus_finance.reduce import reduce_fifo
from decimal import Decimal


def get_account_balance(
    txns: list[data.Transaction], account: str
) -> list[position.Position]:
    inv = inventory.Inventory()

    for txn in sorted(txns, key=lambda t: t.date):
        for posting in txn.postings:
            if posting.account != account:
                continue
            inv.add_position(position.Position(units=posting.units, cost=posting.cost))

    # Reduce to apply FIFO/LIFO/etc.
    return reduce_fifo(inv.get_positions())


def reconcile_transaction(
    txn: data.Directive, index: int, txns: data.Directives
) -> data.Directive:
    if "todo" in txn.meta:
        print(f"ADDRESSING TODO: {txn.meta['todo']}")

        if (
            txn.meta.get("todo_type", "") == "DISTRIBUTION"
            and type(txn) == data.Transaction
        ):
            accts = [p.account for p in txn.postings]
            acct = [a for a in accts if a.startswith("Assets:Investments:")][0]
            print("for account", acct)
            qty = [p.units for p in txn.postings if p.account == acct][0]
            others = [
                t
                for t in txns[: index - 1]
                if type(t) == data.Transaction
                and acct in [p.account for p in t.postings]
            ]
            positions = get_account_balance(others, acct)
            total_balance = sum([p.units.number for p in positions])
            ratio = (qty.number + total_balance) / total_balance

            postings = [
                data.Posting(
                    account="Equity:StockSplit:" + acct.split(":")[-1],
                    units=-amount.Amount(ratio * qty.number, qty.currency),
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

            # Remove old lots at basis and add new ones at adjusted basis
            for p in positions:
                postings.append(
                    data.Posting(
                        account=acct,
                        units=-p.units,
                        cost=(
                            position.Cost(p.cost.number, p.cost.currency, None, None)
                            if p.cost
                            else None
                        ),
                        price=None,
                        flag=None,
                        meta=None,
                    )
                )
                postings.append(
                    data.Posting(
                        account=acct,
                        units=amount.Amount(ratio * p.units.number, p.units.currency),
                        cost=(
                            position.Cost(
                                p.cost.number / ratio, p.cost.currency, None, None
                            )
                            if p.cost
                            else None
                        ),
                        price=None,
                        flag=None,
                        meta=None,
                    )
                )

            meta = {
                k: v for k, v in txn.meta.items() if k != "todo" and k != "todo_type"
            }
            if ratio > 1:
                meta["stock_split"] = f"{ratio} to 1"
            else:
                meta["stock_split"] = f"1 to {1/ratio}"
            return data.Transaction(
                meta=meta,
                date=txn.date,
                flag=txn.flag,
                payee=txn.payee,
                narration=txn.narration,
                tags=txn.tags,
                links=txn.links,
                postings=postings,
            )
        else:
            print(f"  Unhandled TODO type: {txn.meta.get('todo_type', 'none')}")

    return txn
