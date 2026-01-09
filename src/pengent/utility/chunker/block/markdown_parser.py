import json
from typing import List, Any
from mistletoe import Document
from mistletoe.ast_renderer import ASTRenderer
from ....type.rag_block import (
    AnyBlock,
    HeadingBlock,
    TextBlock,
    CodeBlock,
    ListItemBlock,
    TableBlock,
    ImageBlock,
)


class MarkdownBlockParser:
    """Markdownブロックパーサー"""
    renderer = ASTRenderer()

    @staticmethod
    def _extract_text_from_ast(node: Any) -> str:
        """RawTextやLineBreakを含めて再帰抽出"""
        t = node.get("type")
        if t == "RawText":
            return node.get("content", "")
        if t == "LineBreak":
            return "\n"
        text = ""
        for child in node.get("children", []):
            text += MarkdownBlockParser._extract_text_from_ast(child)
        return text

    @classmethod
    def parse(cls, text: str) -> List[AnyBlock]:
        blocks = []
        with cls.renderer as r:
            doc = Document(text)
            ast_json = r.render(doc)  # ASTを取得(ノードのツリー)
            ast = json.loads(ast_json)

        for node in ast.get("children", []):
            t = node.get("type")
            # 見出し
            if t == "Heading":
                level = node.get("level", 1)
                content = "".join(
                    cls._extract_text_from_ast(c) for c in node.get("children", [])
                )
                blocks.append(HeadingBlock(content=content, level=level))

            # 段落
            elif t == "Paragraph":
                # まず画像をチェック
                found_image = False
                for c in node.get("children", []):
                    if c.get("type") == "Image":
                        url = c.get("src", "")
                        # Altテキストは子RawTextを抽出
                        alt = "".join(
                            MarkdownBlockParser._extract_text_from_ast(gc)
                            for gc in c.get("children", [])
                        )
                        blocks.append(ImageBlock(url=url, alt_text=alt))
                        found_image = True
                        break
                if found_image:
                    continue  # 画像として処理したらこのParagraphは完了

                content = "".join(
                    cls._extract_text_from_ast(c) for c in node.get("children", [])
                )
                blocks.append(TextBlock(content=content))

            # コード(フェンス)
            elif t == "CodeFence":
                # children に RawText が入っている想定
                code_content = ""
                for c in node.get("children", []):
                    code_content += c.get("content", "")
                language = node.get("language")
                blocks.append(CodeBlock(content=code_content, language=language))

            # リスト
            elif t == "List":
                for li in node.get("children", []):
                    # 各 ListItem ノード
                    for para in li.get("children", []):
                        if para.get("type") != "Paragraph":
                            continue
                        # Link ノードを探す
                        link_node = next(
                            (
                                c
                                for c in para.get("children", [])
                                if c.get("type") == "Link"
                            ),
                            None,
                        )
                        if link_node:
                            text = "".join(
                                cls._extract_text_from_ast(c)
                                for c in link_node.get("children", [])
                            )
                            url = link_node.get("target")
                            # リンク付きリスト項目として生成
                            blocks.append(
                                ListItemBlock(content=text, url=url, link_text=text)
                            )
                        else:
                            # 通常のリスト項目
                            text = "".join(
                                cls._extract_text_from_ast(c)
                                for c in para.get("children", [])
                            )
                            blocks.append(ListItemBlock(content=text))
            # 画像(Paragraph 内に出現することが多い)
            elif t == "Paragraph":
                for c in node.get("children", []):
                    if c.get("type") == "Image":
                        url = c.get("src", "")
                        alt = c.get("alt", "")
                        blocks.append(ImageBlock(url=url, alt_text=alt))
                        break  # 画像だけ拾いたいならここで抜け

            # テーブル
            elif t == "Table":
                # ヘッダー行
                header = [
                    cls._extract_text_from_ast(c)
                    for c in node.get("header", {}).get("children", [])
                ]
                # ボディ行
                rows = []
                for row in node.get("children", []):
                    # TableRow
                    cells = [
                        cls._extract_text_from_ast(c) for c in row.get("children", [])
                    ]
                    rows.append(cells)
                blocks.append(TableBlock(rows=[header] + rows))

            # 他タイプ(blockquote, thematic_break など)も追加可能
        return blocks
