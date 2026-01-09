import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
)

from pengent.lib import get_logger

logger = get_logger(level=10)

from dotenv import load_dotenv

load_dotenv()

from pengent.tools.api.report.api_report_pdf import ApiReportPdf


def example():
    api = ApiReportPdf()
    current_dir = os.path.dirname(__file__)
    proposal_path = os.path.join(current_dir, "proposal.md")
    logger.debug(f"proposal_path: {proposal_path}")
    with open(proposal_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    api.create_pdf(md_content=md_text)


example()
