import logging
from ctbus_finance.reports import (
    Report,
    report_map,
)
from pathlib import Path
from typing import Iterable


class MonthReports:
    """Collection of reports for a specific month.

    Args:
        month: Integer month index (1-12).
        reports: Optional iterable of reports to initialize the collection.
    """

    def __init__(self, year: int, month: int, reports: Iterable[Report] | None = None) -> None:
        if not 1998 <= year <= 2100:
            raise ValueError("year must be in 1998..2100")
        self.year = year
        if not 1 <= month <= 12:
            raise ValueError("month must be in 1..12")
        self.month = month
        self._reports = list(reports) if reports else []

    def add(self, report: Report) -> None:
        """Add a report to the collection."""
        self._reports.append(report)

    def gather(self, path: str | Path) -> None:
        """Gather reports from a directory."""
        fp = Path(path)
        if not fp.is_dir():
            raise ValueError(f"{fp} is not a directory")
        for fn in fp.glob("*"):
            institution, account_type, account_name = fn.stem.split("_")
            report_type = fn.suffix.lower().replace('.', '')
            report_class = report_map.get(account_type, {}).get(institution, Report)
            self.add(report_class(path = fn, name = account_name, report_type = report_type))

    @classmethod
    def from_directory(cls, path: str | Path) -> "MonthReports":
        """Create a MonthReports instance by gathering reports from a directory."""
        fp = Path(path)
        if not fp.is_dir():
            raise ValueError(f"{fp} is not a directory")
        
        # Assume directory name is in format YYYY_MM
        try:
            year, month = map(int, fp.name.split("_"))
        except ValueError:
            raise ValueError(f"{fp.name} is not in the format YYYY_MM")
        
        month_reports = cls(year, month)
        month_reports.gather(path)
        return month_reports

    @property
    def reports(self) -> list[Report]:
        """Return the list of stored reports."""
        return list(self._reports)

    @property
    def net_value(self) -> float:
        """Aggregate net value of all contained reports."""
        return sum(r.net_value for r in self._reports)