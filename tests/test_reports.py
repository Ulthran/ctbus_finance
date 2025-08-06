from pathlib import Path
import sys

from PyPDF2 import PdfWriter

# Ensure package root is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ctbus_finance import (
    Report,
    MonthReports,
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


def test_net_value_property(tmp_path):
    pdf = tmp_path / "blank.pdf"
    create_blank_pdf(pdf)

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
        report = cls(pdf)
        assert isinstance(report.net_value, (int, float))


def test_month_reports_aggregate(tmp_path):
    pdf = tmp_path / "blank.pdf"
    create_blank_pdf(pdf)

    class DummyReport(Report):
        def __init__(self, value: float) -> None:
            super().__init__(pdf)
            self._value = value

        @property
        def net_value(self) -> float:
            return self._value

    january = MonthReports(1)
    january.add(DummyReport(10))
    january.add(DummyReport(15))

    assert january.net_value == 25
