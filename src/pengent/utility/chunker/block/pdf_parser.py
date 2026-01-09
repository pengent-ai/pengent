import re
from typing import List, Optional
import pdfplumber
from pdfplumber.pdf import PDF
from collections import Counter
from ....lib.custom_logger import get_logger
from ....type.rag_block import (
    AnyBlock,
    HeadingBlock,
    TextBlock,
    TableBlock,
)


class PdfBlockParser:
    """PDFブロックパーサー"""
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
        is_heading_fontsize: bool = False,
        is_heading_lf: bool = False,
        matches_pattern: bool = False,
        heading_patterns: Optional[List[str]] = None,
        pages: Optional[List[int]] = None,
        start_page: Optional[int] = None,  # 1-based
        end_page: Optional[int] = None,  # 1-based, inclusive
    ) -> List[AnyBlock]:
        blocks = []
        compiled_patterns = (
            [re.compile(p) for p in heading_patterns] if heading_patterns else []
        )

        with pdfplumber.open(path) as pdf:
            heading_base = None
            if is_heading_fontsize:
                heading_base = cls._analyze_font_sizes(pdf)
                print(f"Heading font size: {heading_base}")

            for i, page in enumerate(pdf.pages):
                if pages is not None:
                    if i not in pages:
                        continue
                elif start_page is not None or end_page is not None:
                    # ページ番号は1-basedを想定(ユーザー視点)
                    if (
                        not (start_page or 1) - 1
                        <= i
                        <= (end_page or len(pdf.pages)) - 1
                    ):
                        continue

                used_tops = set()
                lines_by_top = {}
                for char in page.chars:
                    top = round(char["top"], 1)
                    lines_by_top.setdefault(top, []).append(char)

                for top, chars in lines_by_top.items():
                    line_text = "".join(
                        c.get("text", "")
                        for c in sorted(chars, key=lambda c: c.get("x", 0))
                    ).strip()

                    avg_size = sum(float(c["size"]) for c in chars) / len(chars)
                    matched = any(p.match(line_text) for p in compiled_patterns)

                    if (is_heading_fontsize and avg_size >= heading_base + 1) or (
                        matches_pattern and matched
                    ):
                        blocks.append(HeadingBlock(content=line_text, level=1))
                        used_tops.add(top)

                # --- 通常段落 ---
                raw_text = page.extract_text()
                if raw_text:
                    paragraphs = raw_text.split("\n\n")
                    for j, para in enumerate(paragraphs):
                        text = para.strip()
                        if not text:
                            continue

                        # 改行ベースの見出し判定
                        is_lf_heading = False
                        if is_heading_lf:
                            is_short = len(text) <= 40
                            prev_blank = j == 0 or not paragraphs[j - 1].strip()
                            next_blank = (
                                j == len(paragraphs) - 1
                                or not paragraphs[j + 1].strip()
                            )
                            is_lf_heading = is_short and prev_blank and next_blank

                        if is_lf_heading:
                            blocks.append(HeadingBlock(content=text, level=1))
                        else:
                            blocks.append(TextBlock(content=text))

                # --- 表 ---
                tables = page.extract_tables()
                for table in tables:
                    if table and len(table) >= 2:
                        blocks.append(TableBlock(rows=table))

        return blocks
