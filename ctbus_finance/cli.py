import argparse
import sys
from datetime import datetime
from ctbus_finance import __version__
from ctbus_finance.db import create_database
from ctbus_finance.ingest import ingest_csv
from pathlib import Path


def main():
    usage_str = "%(prog)s [-h/--help,-v/--version] <subcommand>"
    description_str = (
        "subcommands:\n"
        "  create_db          \tInitialize the database.\n"
        "  ingest_csv         \tIngest a CSV file into the database.\n"
    )

    parser = argparse.ArgumentParser(
        prog="ctbus_finance",
        usage=usage_str,
        description=description_str,
        epilog="",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )

    parser.add_argument("command", help=argparse.SUPPRESS, nargs="?")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=__version__,
    )

    args, remaining = parser.parse_known_args()

    if args.command == "create_db":
        create_database()
    elif args.command == "ingest_csv":
        ingest_csv_parser = argparse.ArgumentParser(
            prog="ingest_csv", description="Ingest a CSV file into the database."
        )
        ingest_csv_parser.add_argument(
            "file_path", help="Path to the CSV file to ingest."
        )
        ingest_csv_parser.add_argument(
            "type",
            help="Type of the CSV file (e.g., accounts, holdings, account_holdings).",
        )
        ingest_csv_parser.add_argument(
            "--date",
            help="Default date (YYYY-MM-DD) to use if date column is missing.",
            default=datetime.today().strftime("%Y-%m-%d"),
        )
        ingest_csv_args = ingest_csv_parser.parse_args(remaining)

        if not ingest_csv_args.file_path:
            sys.stderr.write("File path is required.\n")
            sys.exit(1)
        if not ingest_csv_args.type:
            sys.stderr.write("Type is required.\n")
            sys.exit(1)
        if not Path(ingest_csv_args.file_path).exists():
            sys.stderr.write(f"File {ingest_csv_args.file_path} does not exist.\n")
            sys.exit(1)
        if ingest_csv_args.type not in [
            "accounts",
            "holdings",
            "account_holdings",
            "credit_cards",
            "credit_card_holdings",
        ]:
            sys.stderr.write(f"Type {ingest_csv_args.type} is not recognized.\n")
            sys.exit(1)

        default_date = datetime.strptime(ingest_csv_args.date, "%Y-%m-%d").date()
        ingest_csv(
            fp=Path(ingest_csv_args.file_path),
            table=ingest_csv_args.type,
            default_date=default_date,
        )
    else:
        parser.print_help()
        sys.stderr.write("Unrecognized command.\n")
