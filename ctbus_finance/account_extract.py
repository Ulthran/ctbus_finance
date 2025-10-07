import sys
from beancount.core.data import Commodity
from ctbus_finance.sensitive import starting_accounts
from datetime import datetime
from pathlib import Path


def get_accounts(accts: list[Path]):
    accounts = starting_accounts.copy()
    for fp in accts:
        with open(fp) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(";") or line.startswith("#"):
                    continue
                if line.startswith("Expenses:"):
                    accounts.add(line.split(" ")[0])
                if line.startswith("Income:Dividends:"):
                    accounts.add(line.split(" ")[0])
                if line.startswith("Assets:Investments:"):
                    accounts.add(line.split(" ")[0])
                if line.startswith("Income:CorporateActions:"):
                    accounts.add(line.split(" ")[0])
                if line.startswith("Equity:StockSplit:"):
                    accounts.add(line.split(" ")[0])

    return sorted(accounts)


def get_currency(acct: str) -> str:
    if acct.startswith("Assets:Investments:") or acct.startswith("Equity:StockSplit:"):
        s = acct.split(":")[-1]
        if s == "Cash":
            return "USD"
        return s
    
    return "USD"


def accounts_str(accts: list[Path]):
    return "\n".join(
        [f"1990-01-01 open {account} {get_currency(account)}" for account in get_accounts(accts)]
    )


def get_price_symbols(accts: list[Path]) -> dict[str, str]:
    accounts = get_accounts(accts)
    symbols = {}
    for account in accounts:
        if account.startswith("Assets:Investments:"):
            symbol = account.split(":")[-1]
            real_symbol = symbol
            if symbol == "Cash":
                continue
            if "TICKER" in symbol:
                real_symbol = symbol.replace("TICKER-", "")
            symbols[symbol] = real_symbol
    return symbols


def get_commodities(accts: list[Path]) -> list[Commodity]:
    symbols = get_price_symbols(accts)
    commodities = []
    for symbol, real_symbol in symbols.items():
        commodities.append(Commodity(
            meta={"price": f"USD:yahoo/{real_symbol}"},
            date=datetime.now().date(),
            currency=symbol,
        ))

    return commodities




if __name__ == "__main__":
    print(accounts_str([Path(arg) for arg in sys.argv[1:]]))
    print(get_price_symbols([Path(arg) for arg in sys.argv[1:]]))
