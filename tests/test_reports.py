from pathlib import Path
import sys

from PyPDF2 import PdfWriter

# Ensure package root is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ctbus_finance import (
    Report,
    HSAReport,
    Four03bReport,
    RothIRAReport,
    BrokerageReport,
    CheckingReport,
    SavingsReport,
    CreditCardReport,
    CryptoWalletReport,
    CashReport,
    DigitalWalletReport,
    HealthEquityHSAReport,
    TIAA403bReport,
    VanguardRothIRAReport,
    VanguardBrokerageReport,
    FidelityBrokerageReport,
    CapitalOneCheckingReport,
    CapitalOneSavingsReport,
    CapitalOneCreditCardReport,
    CoinbaseCryptoWalletReport,
    WalletCashReport,
    VenmoDigitalWalletReport,
)


def create_blank_pdf(path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with path.open("wb") as f:
        writer.write(f)


def test_parse_blank(tmp_path):
    pdf = tmp_path / "blank.pdf"
    create_blank_pdf(pdf)
    report = VenmoDigitalWalletReport(pdf)
    assert report.parse() == ""


def test_subclasses():
    account_classes = [
        HSAReport,
        Four03bReport,
        RothIRAReport,
        BrokerageReport,
        CheckingReport,
        SavingsReport,
        CreditCardReport,
        CryptoWalletReport,
        CashReport,
        DigitalWalletReport,
    ]
    for cls in account_classes:
        assert issubclass(cls, Report)

    platform_map = {
        HealthEquityHSAReport: HSAReport,
        TIAA403bReport: Four03bReport,
        VanguardRothIRAReport: RothIRAReport,
        VanguardBrokerageReport: BrokerageReport,
        FidelityBrokerageReport: BrokerageReport,
        CapitalOneCheckingReport: CheckingReport,
        CapitalOneSavingsReport: SavingsReport,
        CapitalOneCreditCardReport: CreditCardReport,
        CoinbaseCryptoWalletReport: CryptoWalletReport,
        WalletCashReport: CashReport,
        VenmoDigitalWalletReport: DigitalWalletReport,
    }
    for subclass, parent in platform_map.items():
        assert issubclass(subclass, parent)
