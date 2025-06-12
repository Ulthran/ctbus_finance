import os
import sys
from pathlib import Path
import subprocess
import pytest

from ctbus_finance import views


@pytest.fixture
def cli_env(tmp_path, monkeypatch):
    db_file = tmp_path / "db.sqlite"
    env = os.environ.copy()
    env["CTBUS_FINANCE_DB_URI"] = f"sqlite:///{db_file}"
    monkeypatch.setenv("CTBUS_FINANCE_DB_URI", f"sqlite:///{db_file}")
    return env


def run_cli(cmd, env):
    subprocess.run([sys.executable, "-m", "ctbus_finance.cli"] + cmd, check=True, env=env)


def ingest_all(env):
    root = Path(__file__).resolve().parents[1] / "example_data"
    files = [
        ("accounts.csv", "accounts"),
        ("holdings.csv", "holdings"),
        ("credit_cards.csv", "credit_cards"),
        ("account_holdings_2024_01_01.csv", "account_holdings"),
        ("credit_card_holdings_2024_01_01.csv", "credit_card_holdings"),
        ("account_holdings_2024_02_01.csv", "account_holdings"),
        ("credit_card_holdings_2024_02_01.csv", "credit_card_holdings"),
        ("account_holdings_2024_03_01.csv", "account_holdings"),
        ("credit_card_holdings_2024_03_01.csv", "credit_card_holdings"),
    ]
    for name, table in files:
        cmd = ["ingest_csv", str(root / name), table]
        if name.startswith("account_holdings_") or name.startswith("credit_card_holdings_"):
            date_parts = name.rstrip(".csv").split("_")[-3:]
            cmd += ["--date", "-".join(date_parts)]
        run_cli(cmd, env)

def test_full_flow(cli_env):
    run_cli(["create_db"], cli_env)
    ingest_all(cli_env)

    accounts = sorted(a[0] for a in views.get_accounts())
    credit_cards = sorted(c[0] for c in views.get_credit_cards())
    trend = views.get_monthly_net_worth()
    net = trend[-1][1]

    assert accounts == ["Brokerage", "Checking", "Roth IRA"]
    assert credit_cards == ["Chase Sapphire Preferred", "Citi Double Cash"]
    assert net == 10058.0
    assert trend == [
        ("2024-01", 6990.0),
        ("2024-02", 8772.0),
        ("2024-03", 10058.0),
    ]
