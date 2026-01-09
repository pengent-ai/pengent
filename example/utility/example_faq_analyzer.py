"""
FAQAnalyzerの使用例

pengent.utility.faq_analyzerパッケージの使い方を示すサンプルコードです。
"""

import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
)

from pengent.lib import get_logger

logger = get_logger(level=10)

from dotenv import load_dotenv

load_dotenv()

from pengent.utility.reader.html_reader import HtmlReader
from pengent.utility.chunker.faq.text_faq_parser import TextFAQParser
from pengent.utility.chunker.faq.faq_analyzer import FAQAnalyser
from pengent.utility.chunker.block.markdown_parser import MarkdownBlockParser
from pengent.utility.chunker.block.html_parser import HttpBlockParser
from pengent.utility.chunker.block.pdf_parser import PdfBlockParser
from pengent.utility.chunker.chunker_factory import create_format


def example_text_parser():
    # faq.txtの内容を読み込む
    with open(
        "example/utility/sample_data/faq.txt", "r", encoding="utf-8"
    ) as file:
        text = file.read()

    blocks = TextFAQParser.parse(text)
    logger.info(f"Parsed {len(blocks)} blocks from text")
    for i, block in enumerate(blocks):
        logger.info(f"Block {i}: {block.type} {block.content[:10]}...")
    analyzer = FAQAnalyser(source_url="example/utility/sample_data/faq.txt")
    faq_pairs = analyzer.extract_faq_pairs_from_blocks(blocks)
    logger.info(f"Extracted {len(faq_pairs)} FAQ pairs from text")
    simple_faqs = analyzer.to_simple_faq_format(faq_pairs)
    logger.info(f"Converted to SimpleFAQ format: {simple_faqs}")


def example_markdown_parser():
    with open(
        "example/utility/sample_data/faq.md", "r", encoding="utf-8"
    ) as file:
        text = file.read()

    blocks = MarkdownBlockParser.parse(text)
    logger.info(f"Parsed {len(blocks)} blocks from markdown")
    analyzer = FAQAnalyser(source_url="example/utility/sample_data/sample2.md")
    faq_pairs = analyzer.extract_faq_pairs_from_blocks(blocks)
    logger.info(f"Extracted {len(faq_pairs)} FAQ pairs from markdown")
    simple_faqs = analyzer.to_simple_faq_format(faq_pairs)
    logger.info(f"Converted to SimpleFAQ format: {simple_faqs}")


def example_html_parser():
    html = HtmlReader.get_content(
        "https://helpx.adobe.com/jp/creative-cloud/faq.html"
    )
    logger.info(
        f"Fetched HTML content from Adobe: {html[:100]}..."
    )  # 最初の100文字だけ表示
    blocks = HttpBlockParser.parse(html)
    logger.info(f"Parsed {len(blocks)} blocks from HTML")
    analyzer = FAQAnalyser(source_url="example/utility/sample_data/sample2.md")
    faq_pairs = analyzer.extract_faq_pairs_from_blocks(blocks)
    logger.info(f"Extracted {len(faq_pairs)} FAQ pairs from markdown")
    simple_faqs = analyzer.to_simple_faq_format(faq_pairs)
    logger.info(f"Converted to SimpleFAQ format: {simple_faqs}")


def example_pdf_parser():
    pdf_path = "example/utility/sample_data/faq.pdf"
    blocks = PdfBlockParser.parse(
        pdf_path, is_heading_fontsize=True, is_heading_lf=True
    )
    logger.info(f"Parsed {len(blocks)} blocks from PDF content")
    logger.info(f"Blocks: {blocks[:10]}")  # 最初の10個のブロックだけ表示


def example_factory_faq():
    docs = create_format(
        rag_format_type="SimpleFAQRagFormat",
        file_type="markdown",
        content=(
            "## Q: サービスの利用料金はいくらですか？\n"
            "A: 基本プランは月額980円です。",
        ),
        parser_config={},
    )
    logger.info(f"Created {len(docs)} chunks from factory function")
    for i, doc in enumerate(docs):
        logger.info(f"doc {i}: {doc}")


# example_text_parser()
# example_markdown_parser()
# example_html_parser()
# example_pdf_parser()
example_factory_faq()
