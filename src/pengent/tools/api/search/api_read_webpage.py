from ....lib.custom_logger import get_logger
from ....utility.reader.html_reader import HtmlReader
from ....utility.chunker.block.html_parser import (
    HttpBlockParser,
    HeadingBlock,
    TextBlock,
    CodeBlock,
    ListItemBlock,
    TableBlock,
    ImageBlock,
)

logger = get_logger()


class ApiHtmlReader:
    """API用HTMLページリーダー"""
    @classmethod
    def get_page_content(cls, url: str) -> str:
        """
        指定されたURLのページ情報を取得する

        Parameters:
            url (str): ページのURL

        Returns:
            str: ページの情報
        """
        html_content = HtmlReader.get_content(url)
        if not html_content:
            raise ValueError(f"指定されたURLのページ情報が取得できませんでした: {url}")

        # html_content
        blocks = HttpBlockParser.parse(html_content)
        lines = []
        for block in blocks:
            if isinstance(block, HeadingBlock):
                lines.append(f"{'#' * block.level} {block.content}\n")
            elif isinstance(block, TextBlock):
                lines.append(f"{block.content}\n")
            elif isinstance(block, CodeBlock):
                language = block.language if block.language else ""
                lines.append(
                    f"```{language}\n{block.content}\n```\n"
                )
            elif isinstance(block, ListItemBlock):
                lines.append(f"- {block.content}")
            elif isinstance(block, TableBlock):
                for row in block.rows:
                    lines.append(f"| {' | '.join(row)} |")
            elif isinstance(block, ImageBlock):
                lines.append(f"![{block.alt_text}]({block.url})")

        return "\n".join(lines)
