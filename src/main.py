import json

from common.echo_miner import EchoMiner
from common.report_processor.advanced_report_processor import AdvancedReportProcessor

miner = EchoMiner(report_processor=AdvancedReportProcessor())

miner.process_report(100001)

print(json.dumps(miner.processed_reports, indent=4, ensure_ascii=False))
