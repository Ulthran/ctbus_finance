import subprocess as sp
from ctbus_finance.dividend_accounts import dividend_accounts_str
from ctbus_finance.expense_accounts import expense_accounts_str
from ctbus_finance.investment_accounts import investment_accounts_str
from pathlib import Path


if __name__ == "__main__":
    for fp in Path("/home/ctbus/ctbus_finance/logs").glob("*.log"):
        fp.unlink()

    csvs = list(Path("/home/ctbus/ctbus_finance/csv/").glob("*.csv"))
    beancounts = [
        Path("/home/ctbus/ctbus_finance/beancount") / (csv.stem + ".beancount")
        for csv in csvs
    ]
    for csv, beancount in zip(csvs, beancounts):
        result = sp.run(
            [
                "bean-extract",
                "/home/ctbus/ctbus_finance/ctbus_finance/importers/config.py",
                str(csv),
            ],
            capture_output=True,
            text=True,
        )
        with open(beancount, "w") as f:
            f.write(result.stdout)
        if result.stderr:
            with open(
                f"/home/ctbus/ctbus_finance/logs/{csv.stem}.log", "w"
            ) as log_file:
                log_file.write(result.stderr)

    with open(
        "/home/ctbus/ctbus_finance/beancount/expense_accounts.beancount", "w"
    ) as f:
        f.write(expense_accounts_str(beancounts))

    with open(
        "/home/ctbus/ctbus_finance/beancount/dividend_accounts.beancount", "w"
    ) as f:
        f.write(dividend_accounts_str(beancounts))

    with open(
        "/home/ctbus/ctbus_finance/beancount/investment_accounts.beancount", "w"
    ) as f:
        f.write(investment_accounts_str(beancounts))

    result = sp.run(
        ["bean-check", "/home/ctbus/ctbus_finance/all.beancount"],
        capture_output=True,
        text=True,
    )
    with open("/home/ctbus/ctbus_finance/check.txt", "w") as f:
        f.write(result.stderr)
    with open("/home/ctbus/ctbus_finance/check.txt") as f:
        num_issues = len(f.readlines()) / 4
    if num_issues > 0:
        print(f"Found {num_issues} issues in check.txt")
