import sys
from pathlib import Path

from ctbus_finance import dividend_accounts


def get_investment_accounts(accts: list[Path]):
    investment_accounts = set()
    for fp in accts:
        with open(fp) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(";") or line.startswith("#"):
                    continue
                if line.startswith("Assets:Investments:"):
                    investment_accounts.add(line.split(" ")[0])

    return sorted(investment_accounts)


def get_currency(acct: str) -> str:
    s = acct.split(":")[-1]
    if s == "Cash":
        return "USD"
    return s


def investment_accounts_str(accts: list[Path]):
    return "\n".join(
        [f"2020-01-01 open {account} {get_currency(account)}" for account in get_investment_accounts(accts)]
    )


if __name__ == "__main__":
    print(investment_accounts_str([Path(arg) for arg in sys.argv[1:]]))
