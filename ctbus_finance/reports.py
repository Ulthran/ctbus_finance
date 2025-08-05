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


class FidelityReport(Report):
    """Parser for Fidelity PDF statements."""


class VanguardReport(Report):
    """Parser for Vanguard PDF statements."""


class CapitalOneReport(Report):
    """Parser for Capital One PDF statements."""
