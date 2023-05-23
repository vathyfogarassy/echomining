from io import TextIOWrapper
from typing import Optional

import py7zr as py7zr

from data import REPORTS_PATH, determine_id


class ReportLoader:
    def __init__(self, path: Optional[str] = REPORTS_PATH):
        self._path = path
        self._reports = {}

    @property
    def keys(self):
        return self._reports.keys()

    def load_reports(self):
        if not self._reports:
            with py7zr.SevenZipFile(self._path, mode="r") as z:
                reports = z.readall()

                for report_name, report in reports.items():
                    self._reports[determine_id(report_name)] = report

    def get_report(self, report_id):
        if self._reports:
            if report_id in self.keys:
                return TextIOWrapper(self._reports[report_id], encoding="utf-8").read()
