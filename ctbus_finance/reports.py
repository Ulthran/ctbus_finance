import csv
import logging
import re
from abc import ABC
from pathlib import Path
from PyPDF2 import PdfReader
from typing import Any


class Report(ABC):
    """Base class for PDF account reports."""

    def __init__(self, path: str | Path, name: str, report_type: str):
        self.path = Path(path)
        self.name = name
        self.report_type = report_type

        self._net_value: float = 0.0

        self.parse()

    def parse(self):
        raise NotImplementedError(
            f"Subclasses must implement the parse method for {self.report_type} reports."
        )
    
    @property
    def net_value(self) -> float:
        """Return the net value of the report."""
        return self._net_value


class ReportHSA(Report):
    """Base class for HSA account statements."""


class Report403b(Report):
    """Base class for 403b account statements."""


class ReportRothIRA(Report):
    """Base class for Roth IRA account statements."""


class ReportBrokerage(Report):
    """Base class for brokerage account statements."""


class ReportChecking(Report):
    """Base class for checking account statements."""


class ReportSavings(Report):
    """Base class for savings account statements."""


class ReportCreditCard(Report):
    """Base class for credit card statements."""


class ReportCryptoWallet(Report):
    """Base class for cryptocurrency wallet statements."""


class ReportCash(Report):
    """Base class for cash statements."""


class ReportDigitalWallet(Report):
    """Base class for digital wallet statements."""


class HealthEquityReportHSA(ReportHSA):
    """Parser for HealthEquity HSA PDF statements."""


class TIAAReport403b(Report403b):
    """Parser for TIAA 403b PDF statements."""


class VanguardReportRothIRA(ReportRothIRA):
    """Parser for Vanguard Roth IRA PDF statements."""


class VanguardReportBrokerage(ReportBrokerage):
    """Parser for Vanguard brokerage PDF statements."""


class FidelityReportBrokerage(ReportBrokerage):
    """Parser for Fidelity brokerage PDF statements."""
    def parse(self):
        if self.report_type == "csv":
            return self._parse_csv()
        else:
            return self._parse_pdf()
        
    def _parse_csv(self):
        with self.path.open(newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            transactions = [row for row in reader]
        return transactions
    
    def _parse_pdf(self):
        with self.path.open("rb") as pdf_file:
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
                
        # Search for "Your Account Value: $XX.XX"
        match = re.search(r"Your Account Value:\s*\$?([\d,]+\.\d{2})", text)
        if match:
            self._net_value = float(match.group(1).replace(',', ''))
        else:
            logging.warning(f"Could not find account value in {self.path}")

        return text
    

class CapitalOneReportChecking(ReportChecking):
    """Parser for Capital One checking PDF statements."""
    

class CapitalOneReportSavings(ReportSavings):
    """Parser for Capital One savings PDF statements."""


class CapitalOneReportCreditCard(ReportCreditCard):
    """Parser for Capital One credit card PDF statements."""


class CoinbaseReportCryptoWallet(ReportCryptoWallet):
    """Parser for Coinbase crypto wallet PDF statements."""


class WalletReportCash(ReportCash):
    """Parser for wallet cash PDF statements."""


class VenmoReportDigitalWallet(ReportDigitalWallet):
    """Parser for Venmo digital wallet PDF statements."""


report_map: dict[str, dict[str, type[Report]]] = {
    "HSA": {
        "HealthEquity": HealthEquityReportHSA,
    },
    "403b": {
        "TIAA": TIAAReport403b,
    },
    "RothIRA": {
        "Vanguard": VanguardReportRothIRA,
    },
    "Brokerage": {
        "Vanguard": VanguardReportBrokerage,
        "Fidelity": FidelityReportBrokerage,
    },
    "Checking": {
        "CapitalOne": CapitalOneReportChecking,
    },
    "Savings": {
        "CapitalOne": CapitalOneReportSavings,
    },
    "CreditCard": {
        "CapitalOne": CapitalOneReportCreditCard,
    },
    "CryptoWallet": {
        "Coinbase": CoinbaseReportCryptoWallet,
    },
    "Cash": {
        "Wallet": WalletReportCash,
    },
    "DigitalWallet": {
        "Venmo": VenmoReportDigitalWallet,
    },
}