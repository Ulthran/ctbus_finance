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
