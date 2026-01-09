from bs4 import BeautifulSoup, NavigableString
from ....lib import get_logger

logger = get_logger()
from ....type.rag_block import (
    HeadingBlock,
    TextBlock,
    CodeBlock,
    ListItemBlock,
    TableBlock,
    ImageBlock,
)


class HttpBlockParser:
    """HTMLコンテンツをRAG用のBlockにパースするクラス"""
    @classmethod
    def _remove_noise(
        cls,
        soup: BeautifulSoup,
        exclude_tags: list = None,
    ) -> BeautifulSoup:
        if exclude_tags is None:
            exclude_tags = ["nav", "footer", "aside", "script", "style"]
        logger.info(f"remove_noise: {len(str(soup))}")
        for tag in soup(exclude_tags):
            tag.decompose()
        logger.debug(f"remove_noise after: {len(str(soup))}")
        return soup

    @classmethod
    def parse(
        cls,
        html: str,
        include_tags: list = None,
        exclude_tags: list = None,
    ):
        if include_tags is None:
            include_tags = [
                "h1",
                "h2",
                "h3",
                "p",
                "img",
                "a",
                "li",
                "table",
                "pre",
                "code",
            ]
        if exclude_tags is None:
            exclude_tags = ["nav", "footer", "aside", "script", "style"]
        logger.info("Parsing HTML content")
        soup = BeautifulSoup(html, "html.parser")
        soup = cls._remove_noise(soup, exclude_tags=exclude_tags)
        main = soup.find("article") or soup.body
        if not main:
            logger.error("Main content not found.")
            return []

        result = []
        for elem in soup.find_all(include_tags):
            if elem.name in ["h1", "h2", "h3"]:
                text = elem.get_text(strip=True)
                result.append(HeadingBlock(level=int(elem.name[1]), content=text))
            elif elem.name == "p":
                content = ""
                for child in elem.contents:
                    if isinstance(child, NavigableString):
                        content += str(child)
                    elif child.name == "code":
                        content += f"`{child.get_text(strip=True)}`"
                    else:
                        content += child.get_text(strip=True)
                if content.strip():
                    result.append(TextBlock(content=content.strip()))
            elif elem.name == "pre":
                # nested codeがある場合でも fallback できるように
                code = elem.get_text().strip()
                if code:
                    result.append(CodeBlock(language=None, content=code))
            elif elem.name == "div":
                # 子要素がない or テキストが直接ある
                if not elem.find():  # 子タグが無い
                    content = elem.get_text(strip=True)
                    if content:
                        result.append(TextBlock(content=content.strip()))
            elif elem.name == "img":
                result.append(
                    ImageBlock(url=elem.get("src"), alt_text=elem.get("alt", ""))
                )
            elif elem.name == "li":
                # 子要素がない or テキストが直接ある
                if not elem.find():  # 子タグが無い
                    text = elem.get_text(strip=True)
                    if text:
                        result.append(ListItemBlock(content=text))

            elif elem.name == "table":
                rows = []
                for tr in elem.find_all("tr"):
                    row = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                    if row:
                        rows.append(row)
                if rows:
                    result.append(TableBlock(rows=rows))

        logger.debug(f"Parsed content length: {len(result)} items")
        return result
