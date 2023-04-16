from common.report_processor.abstract_report_processor import AbstractReportProcessor


class NullReportProcessor(AbstractReportProcessor):
    def process(self, text):
        self._processed_text = text
