from pathlib import Path
import sys

from PyPDF2 import PdfWriter

# Ensure package root is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ctbus_finance import (
    Report,
    FidelityReport,
    VanguardReport,
    CapitalOneReport,
)


def create_blank_pdf(path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with path.open("wb") as f:
        writer.write(f)


def test_parse_blank(tmp_path):
    pdf = tmp_path / "blank.pdf"
    create_blank_pdf(pdf)
    report = FidelityReport(pdf)
    assert report.parse() == ""


def test_subclasses():
    for cls in (FidelityReport, VanguardReport, CapitalOneReport):
        assert issubclass(cls, Report)
