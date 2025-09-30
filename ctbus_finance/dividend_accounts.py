import sys
from pathlib import Path


def get_dividend_accounts(accts: list[Path]):
    dividend_accounts = set()
    for fp in accts:
        with open(fp) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(";") or line.startswith("#"):
                    continue
                if line.startswith("Income:Dividends:"):
                    dividend_accounts.add(line.split(" ")[0])

    return sorted(dividend_accounts)


def dividend_accounts_str(accts: list[Path]):
    return "\n".join(
        [f"2020-01-01 open {account} USD" for account in get_dividend_accounts(accts)]
    )


if __name__ == "__main__":
    print(dividend_accounts_str([Path(arg) for arg in sys.argv[1:]]))
