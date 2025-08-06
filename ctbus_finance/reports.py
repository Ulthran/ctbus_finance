from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PyPDF2 import PdfReader


class Report:
    """Base class for PDF account reports."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def parse(self) -> str:
        """Return the text extracted from the PDF report."""
        reader = PdfReader(str(self.path))
        texts: Iterable[str] = (page.extract_text() or "" for page in reader.pages)
        return "\n".join(texts).strip()

    @property
    def net_value(self) -> float:
        """Net monetary value represented by this report."""
        return 0.0


class MonthReports:
    """Collection of reports for a specific month.

    Args:
        month: Integer month index (1-12).
        reports: Optional iterable of reports to initialize the collection.
    """

    def __init__(self, month: int, reports: Iterable[Report] | None = None) -> None:
        if not 1 <= month <= 12:
            raise ValueError("month must be in 1..12")
        self.month = month
        self._reports = list(reports) if reports else []

    def add(self, report: Report) -> None:
        """Add a report to the collection."""
        self._reports.append(report)

    @property
    def reports(self) -> list[Report]:
        """Return the list of stored reports."""
        return list(self._reports)

    @property
    def net_value(self) -> float:
        """Aggregate net value of all contained reports."""
        return sum(r.net_value for r in self._reports)


class HSAReport(Report):
    """Base class for HSA account statements."""


class Four03bReport(Report):
    """Base class for 403b account statements."""


class RothIRAReport(Report):
    """Base class for Roth IRA account statements."""


class BrokerageReport(Report):
    """Base class for brokerage account statements."""


class CheckingReport(Report):
    """Base class for checking account statements."""


class SavingsReport(Report):
    """Base class for savings account statements."""


class CreditCardReport(Report):
    """Base class for credit card statements."""


class CryptoWalletReport(Report):
    """Base class for cryptocurrency wallet statements."""


class CashReport(Report):
    """Base class for cash statements."""


class DigitalWalletReport(Report):
    """Base class for digital wallet statements."""


class HealthEquityHSAReport(HSAReport):
    """Parser for HealthEquity HSA PDF statements."""


class TIAA403bReport(Four03bReport):
    """Parser for TIAA 403b PDF statements."""


class VanguardRothIRAReport(RothIRAReport):
    """Parser for Vanguard Roth IRA PDF statements."""


class VanguardBrokerageReport(BrokerageReport):
    """Parser for Vanguard brokerage PDF statements."""


class FidelityBrokerageReport(BrokerageReport):
    """Parser for Fidelity brokerage PDF statements."""


class CapitalOneCheckingReport(CheckingReport):
    """Parser for Capital One checking PDF statements."""


class CapitalOneSavingsReport(SavingsReport):
    """Parser for Capital One savings PDF statements."""


class CapitalOneCreditCardReport(CreditCardReport):
    """Parser for Capital One credit card PDF statements."""


class CoinbaseCryptoWalletReport(CryptoWalletReport):
    """Parser for Coinbase crypto wallet PDF statements."""


class WalletCashReport(CashReport):
    """Parser for wallet cash PDF statements."""


class VenmoDigitalWalletReport(DigitalWalletReport):
    """Parser for Venmo digital wallet PDF statements."""
