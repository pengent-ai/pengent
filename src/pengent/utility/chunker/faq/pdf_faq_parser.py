from typing import List, Optional
import pdfplumber
from pdfplumber.pdf import PDF
from collections import Counter
from ....lib.custom_logger import get_logger
from ....type.rag_block import (
    AnyBlock,
    HeadingBlock,
    TextBlock,
)


class PdfFAQParser:
    """PDF FAQパーサー"""
    logger = get_logger()

    @classmethod
    def _analyze_font_sizes(cls, pdf: PDF) -> float:
        sizes = []
        for page in pdf.pages:
            for char in page.chars:
                sizes.append(round(char["size"], 1))  # 小数点1桁に丸めて正規化
        counter = Counter(sizes)

        # ログ出力(任意)
        cls.logger.debug("Font Sizes List:")
        for size, count in counter.most_common():
            cls.logger.debug(f" - size={size}: {count} chars")

        # 最頻出サイズを標準本文サイズとみなして返す
        if counter:
            most_common_size = counter.most_common(1)[0][0]
            return most_common_size
        else:
            cls.logger.warning("No font sizes found in the PDF.")
            return False


@classmethod
def parse(
    cls,
    path: str,
    pages: Optional[List[int]] = None,
    start_page: Optional[int] = None,  # 1-based
    end_page: Optional[int] = None,  # 1-based, inclusive
    table_question_index: Optional[int] = None,
    table_answer_index: Optional[int] = None,
) -> List[AnyBlock]:
    blocks = []

    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            if pages is not None:
                if i not in pages:
                    continue
            elif start_page is not None or end_page is not None:
                # ページ番号は1-basedを想定
                if not (start_page or 1) - 1 <= i <= (end_page or len(pdf.pages)) - 1:
                    continue

            # テキストの段落ごとに処理
            raw_text = page.extract_text()
            if raw_text:
                paragraphs = raw_text.split("\n\n")
                for para in paragraphs:
                    text = para.strip()
                    if not text:
                        continue

                    if text.startswith(("Q:", "Q．", "Q.", "質問", "？", "?")):
                        blocks.append(HeadingBlock(content=text))
                    elif text.startswith(("A:", "A．", "A.", "回答", "答え")):
                        blocks.append(TextBlock(content=text))
                    else:
                        blocks.append(TextBlock(content=text))

            # 表の処理(必要であれば)
            if table_question_index is not None and table_answer_index is not None:
                tables = page.extract_tables()
                for table in tables:
                    if table and len(table) >= 2:
                        for row in table:
                            if table_question_index < len(row):
                                question = row[table_question_index].strip()
                                blocks.append(HeadingBlock(content=question))
                            if table_answer_index < len(row):
                                answer = row[table_answer_index].strip()
                                blocks.append(TextBlock(content=answer))
    return blocks
