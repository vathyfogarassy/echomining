from abc import abstractmethod


class AbstractReportProcessor:
    def __init__(self):
        self._processed_text = None

    @abstractmethod
    def process(self, text):
        pass

    @property
    def processed_text(self):
        return self._processed_text
