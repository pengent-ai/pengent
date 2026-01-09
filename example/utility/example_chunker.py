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
from pengent.utility.chunker.text.text_chunker import TextChunker
from pengent.utility.chunker.block.block_chunker import BlockChunker
from pengent.utility.chunker.block.markdown_parser import MarkdownBlockParser
from pengent.utility.chunker.block.html_parser import HttpBlockParser
from pengent.utility.chunker.block.pdf_parser import PdfBlockParser
from pengent.utility.chunker.chunker_factory import create_format


def example_text_chunker():
    # sample.txtの内容を読み込む
    with open(
        "example/utility/sample_data/sample2.txt", "r", encoding="utf-8"
    ) as file:
        text = file.read()
    chunker = TextChunker(
        max_tokens=512, overlap=50, heading_patterns=[r"^\d+\.\s.+", r"^■\s.+"]
    )
    chunks = chunker.split(text)
    logger.info(f"Total chunks created: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        logger.info("----------------------------")  # 最初の50文字だけ表示
        logger.info(f"Chunk {i}: {chunk}")


def example_markdown_block_parser():
    with open(
        "example/utility/sample_data/sample2.md", "r", encoding="utf-8"
    ) as file:
        text = file.read()

    blocks = MarkdownBlockParser.parse(text)
    chunker = BlockChunker(
        max_tokens=512, overlap=50, title="Sample Markdown", heading_level=2
    )
    chunks = chunker.split_from_blocks(blocks)
    logger.info(f"Total chunks created: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        logger.info("----------------------------")  # 最初の50文字だけ表示
        logger.info(f"Chunk {i}: {chunk}")


def example_http_block_parser():
    html = HtmlReader.get_content(
        "https://qiita.com/minorun365/items/b2990a7228e8cc4ed025"
    )
    logger.info(
        f"Fetched HTML content from Qiita: {html[:100]}..."
    )  # 最初の100文字だけ表示
    blocks = HttpBlockParser.parse(html)
    logger.info(f"Parsed {len(blocks)} blocks from HTML content")
    logger.info(f"Blocks: {blocks[:3]}")  # 最初の3つのブロックだけ表示
    chunker = BlockChunker(
        max_tokens=512, overlap=50, title="Sample Markdown", heading_level=2
    )
    chunks = chunker.split(blocks)
    for i, chunk in enumerate(chunks):
        logger.info("----------------------------")  # 最初の50文字だけ表示
        logger.info(f"Chunk {i}: {chunk}")


def example_pdf_block_parser():
    pdf_path = "example/utility/sample_data/sample4.pdf"
    blocks = PdfBlockParser.parse(
        pdf_path, is_heading_fontsize=True, is_heading_lf=True
    )
    logger.info(f"Parsed {len(blocks)} blocks from PDF content")
    logger.info(f"Blocks: {blocks[:3]}")  # 最初の3つのブロックだけ表示
    chunker = BlockChunker(
        max_tokens=512, overlap=50, title="Sample PDF", heading_level=2
    )
    chunks = chunker.split(blocks)
    for i, chunk in enumerate(chunks):
        logger.info("----------------------------")  # 最初の50文字だけ表示
        logger.info(f"Chunk {i}: {chunk}")


def example_factory_chunker():
    docs = create_format(
        rag_format_type="DocStructuredRagFormat",
        file_type="markdown",
        content="## Sample Markdown\n\nThis is a sample markdown content.",
        parser_config={
            "max_tokens": 512,
            "overlap": 50,
            "title": "Sample Markdown",
        },
    )
    logger.info(f"Created {len(docs)} chunks from factory function")
    for i, doc in enumerate(docs):
        logger.info(f"doc {i}: {doc}")


# example_text_chunker()
# example_markdown_block_parser()
# example_http_block_parser()
# example_pdf_block_parser()
example_factory_chunker()
