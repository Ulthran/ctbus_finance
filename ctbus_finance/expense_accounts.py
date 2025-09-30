import sys
from pathlib import Path


def get_expense_accounts(accts: list[Path]):
    expense_accounts = set()
    for fp in accts:
        with open(fp) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(";") or line.startswith("#"):
                    continue
                if line.startswith("Expenses:"):
                    expense_accounts.add(line.split(" ")[0])

    return sorted(expense_accounts)


def expense_accounts_str(accts: list[Path]):
    return "\n".join(
        [f"2020-01-01 open {account} USD" for account in get_expense_accounts(accts)]
    )


if __name__ == "__main__":
    print(expense_accounts_str([Path(arg) for arg in sys.argv[1:]]))
