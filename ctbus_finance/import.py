import subprocess as sp
from beancount.core import data
from beancount.loader import load_file
from beancount.parser import printer
from beangulp.extract import extract_from_file
from beangulp.identify import identify
from ctbus_finance.account_extract import accounts_str, get_commodities
from ctbus_finance.importers.config import CONFIG
from ctbus_finance.reconcile import reconcile_transaction
from ctbus_finance.starting_balances import starting_balances
from datetime import datetime
from pathlib import Path


if __name__ == "__main__":
    logs_dir = Path("/home/ctbus/ctbus_finance/logs")
    logs_dir.mkdir(exist_ok=True)

    # Clean old logs
    for fp in logs_dir.glob("*.log"):
        fp.unlink()

    csvs = list(Path("/home/ctbus/ctbus_finance/csv/").glob("*.csv"))
    beancounts = [
        Path("/home/ctbus/ctbus_finance/beancount") / (csv.stem + ".beancount")
        for csv in csvs
    ]
    transactions_fp = Path("/home/ctbus/ctbus_finance/beancount/transactions.beancount")
    manual_fp = Path("/home/ctbus/ctbus_finance/beancount/manual.beancount")

    # Import CSVs
    txns: data.Directives = starting_balances()
    for csv, beancount in zip(csvs, beancounts):
        try:
            
            importer = identify(CONFIG, str(csv))

            if not importer:
                print(f"No importer found for {csv}")
                continue

            entries = extract_from_file(importer, str(csv), [])
            txns.extend(entries)
        except Exception as e:
            # Log errors per file
            print(f"Error processing {csv}: {e}")
            raise

    # Reconcile TODOs
    txns = [reconcile_transaction(txn, i, txns) for i, txn in enumerate(txns)]
    with open(transactions_fp, "w") as f:
        for entry in sorted(txns, key=lambda x: x.date):
            f.write(printer.format_entry(entry))
            f.write("\n")  # add a blank line between entries

    # Generate account file
    with open(
        "/home/ctbus/ctbus_finance/beancount/accounts.beancount", "w"
    ) as f:
        f.write(accounts_str([transactions_fp, manual_fp]))

    # Generate commodities file
    commodities = get_commodities([transactions_fp, manual_fp])
    with open(
        "/home/ctbus/ctbus_finance/beancount/commodities.beancount", "w"
    ) as f:
        for commodity in commodities:
            f.write(printer.format_entry(commodity))

    if True:
    # Generate prices file
        prices_fp = Path(f"/home/ctbus/ctbus_finance/beancount/prices/{datetime.now().strftime('%Y_%m_%d')}.beancount")
        prices_fp.unlink(missing_ok=True)

        result = sp.run(
            ["bean-price", "/home/ctbus/ctbus_finance/all.beancount", "-w", "8"],
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            text=True,
        )
        print(f"bean-price: {result.stderr}")
        with open(prices_fp, "w") as f:
            f.write(result.stdout)
