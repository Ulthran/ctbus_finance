import sys
from ctbus_finance.month import MonthReports
from pathlib import Path


def main(args = sys.argv[1:]) -> None:
    if len(args) != 1:
        print("Usage: python demo.py <path_to_reports_directory>")
        sys.exit(1)

    reports_path = Path(args[0])
    if not reports_path.is_dir():
        print(f"Error: {reports_path} is not a valid directory.")
        sys.exit(1)

    all_reports: list[MonthReports] = []
    for dir in reports_path.iterdir():
        if dir.is_dir() and dir.name.startswith("20"):
            try:
                month_reports = MonthReports.from_directory(dir)
                print(f"Gathered {len(month_reports.reports)} reports for {month_reports.year}-{month_reports.month:02d}.")
                all_reports.append(month_reports)
            except ValueError as e:
                print(f"Skipping {dir.name}: {e}")
            continue

    for month_report in all_reports:
        for report in month_report.reports:
            print(f"Report: {report.name}, Type: {report.report_type}, Path: {report.path}, Net Value: {report.net_value}")
        print(f"Total Net Value for {month_report.year}-{month_report.month:02d}: {sum(r.net_value for r in month_report.reports)}")


if __name__ == "__main__":
    main()