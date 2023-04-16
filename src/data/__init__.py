import os

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

REPORTS_FILE = "echo_reports.7z"
REPORTS_PATH = os.path.join(DATA_DIR, REPORTS_FILE)

DICTIONARY_FILE = "dictionary.json"
DICTIONARY_PATH = os.path.join(DATA_DIR, DICTIONARY_FILE)


def determine_id(report_name):
    return int(report_name[: -len(".txt")])
