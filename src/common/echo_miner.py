import json
from typing import Optional

import flatdict
import jellyfish
import pandas

from common.report_loader.report_loader import ReportLoader
from common.report_processor.abstract_report_processor import AbstractReportProcessor
from common.report_processor.null_report_processor import NullReportProcessor
from data import DICTIONARY_PATH


class EchoMiner:
    # UH_DICT_THRESHOLD = 0.1
    UH_DICT_THRESHOLD = 0.05

    def __init__(self, *, report_processor: Optional[AbstractReportProcessor] = None):
        self._report_loader = ReportLoader()
        self._report_loader.load_reports()

        self._dictionary = self._load_dictionary()

        self._report_processor = report_processor or NullReportProcessor()

        self._processed_reports = {}

    @property
    def processed_reports(self):
        return self._processed_reports

    def process_report(self, report_id):
        report = self._report_loader.get_report(report_id)

        if report:
            self._report_processor.process(report)
            self._processed_reports[report_id] = self._determine_matched_terms(
                self._report_processor.processed_text
            )

    def process_reports(self):
        [self.process_report(report_id) for report_id in self._report_loader.keys]

    def _determine_matched_terms(self, processed_report):
        for paragraph_id, term_types in processed_report.items():
            for term_type, terms in term_types.items():
                for index, term in enumerate(terms):
                    processed_report[paragraph_id][term_type][index][
                        "matched_term"
                    ] = self._find_in_dict(
                        processed_report[paragraph_id][term_type][index]["candidate"]
                    )

        return processed_report

    def _find_in_dict(self, term):
        def dist(w1, w2):
            return 1 - (jellyfish.jaro_winkler_similarity(w1, w2))

        found = {
            matched_term: dist(term, matched_term)
            for key in self._dictionary.keys()
            for matched_term in self._dictionary[key]
            if dist(term, matched_term) < self.UH_DICT_THRESHOLD
        }

        return (
            [
                key
                for key, value in self._dictionary.items()
                if min(found, key=found.get) in value
            ][0]
            if found
            else ""
        )

    @staticmethod
    def _load_dictionary():
        with open(DICTIONARY_PATH, encoding="utf-8") as dict_file:
            return json.load(dict_file)
