import os
import re
import zlib
import base64

import markdown
import pdfkit

from ....lib.custom_logger import get_logger

logger = get_logger()


def _encode64(data):
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    result = ""
    i = 0
    while i < len(data):
        b1 = data[i]
        b2 = data[i + 1] if i + 1 < len(data) else 0
        b3 = data[i + 2] if i + 2 < len(data) else 0

        c1 = b1 >> 2
        c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
        c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
        c4 = b3 & 0x3F

        result += alphabet[c1 & 0x3F]
        result += alphabet[c2 & 0x3F]
        result += alphabet[c3 & 0x3F]
        result += alphabet[c4 & 0x3F]

        i += 3
    return result


def _encode_plantuml(text: str):
    """PlantUML用エンコード関数(公式仕様に基づく)"""
    data = zlib.compress(text.encode("utf-8"))[2:-4]
    return _encode64(data)


def _kroki_encode(text: str) -> str:
    zlibbed = zlib.compress(text.encode("utf-8"))  # 圧縮はヘッダつきでOK
    b64 = base64.urlsafe_b64encode(zlibbed).decode("utf-8")  # base64url(+ / = 対応済)
    return b64.rstrip("=")  # URLで=を削除


class ApiReportPdf:
    """
    MarkdownからPDFレポートを生成するクラス
    """
    TOOL_PATH_WKHTMLTOPDF = os.getenv("TOOL_PATH_WKHTMLTOPDF")
    config = pdfkit.configuration(wkhtmltopdf=TOOL_PATH_WKHTMLTOPDF)

    @staticmethod
    def _plantuml_url(uml_text):
        """
        PlantUMLの図形を公式ツールのURLを生成するメソッド
        """
        encoded = _encode_plantuml(uml_text)
        return f"http://www.plantuml.com/plantuml/svg/{encoded}"

    @staticmethod
    def mermaid_url(mermaid_code: str) -> str:
        encoded = _kroki_encode(mermaid_code)
        return f"https://kroki.io/mermaid/svg/{encoded}"

    @classmethod
    def convert_md2html(
        cls, md_content, is_plantuml=True, is_mermaid=True, is_sdxl=False
    ):
        """
        MarkdownからHTMLに変換するメソッド
        """

        def plantuml_replacer(match):
            uml_code = match.group(1).strip()
            url = cls._plantuml_url(uml_code)
            logger.debug(f"PlantUML URL: {url}")
            return f'<img src="{url}" alt="PlantUML Diagram" />'

        def mermaid_replacer(match):
            mermaid_code = match.group(1).strip()
            url = cls.mermaid_url(mermaid_code)
            logger.debug(f"Mermaid URL: {url}")
            return f'<img src="{url}" alt="Mermaid Diagram" />'

        def sdxl_replacer(match):
            sdxl_prompt = match.group(1).strip()  # noqa: F841
            return ""
            # url = sdxl_url(sdxl_prompt)
            # if url:
            #     print(f"SDXL URL: {url}")
            #     return f'<img src="{url}" alt="{sdxl_prompt}" />'

        if is_plantuml:
            # PlantUMLのコードを置換
            md_content = re.sub(
                r"```plantuml(.*?)```", plantuml_replacer, md_content, flags=re.DOTALL
            )

        if is_mermaid:
            # Mermaidのコードを置換
            md_content = re.sub(
                r"```mermaid(.*?)```", mermaid_replacer, md_content, flags=re.DOTALL
            )

        if is_sdxl:
            # SDXLのコードを置換
            md_content = re.sub(
                r"```sdxl(.*?)```", sdxl_replacer, md_content, flags=re.DOTALL
            )

        # HTML本体生成
        html_body = markdown.markdown(
            md_content, extensions=["fenced_code", "codehilite", "tables"]
        )
        html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji",
                    "Noto Sans CJK JP", "IPAPGothic", "Meiryo", sans-serif;
                    line-height: 1.6;
                    max-width: 800px;
                    margin: auto;
                    padding: 2em;
                }}
                h1 {{
                    text-align: center;
                    font-size: 2em;
                    margin-top: 1.5em;
                    margin-bottom: 1em;
                    border-bottom: 2px solid #ccc;
                }}
                img {{
                    display: block;
                    margin: 1em auto;
                    max-width: 100%;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 1em 0;
                }}
                th, td {{
                    border: 1px solid #999;
                    padding: 0.5em;
                    text-align: left;
                    background: #fff;
                }}
                th {{
                    background: #eee;
                }}
            </style>
        </head>
        <body>{html_body}</body>
        </html>
        """  # noqa: E501
        return html

    @classmethod
    def create_pdf(
        cls,
        md_content,
        output_file="output.pdf",
        is_plantuml=True,
        is_mermaid=True,
        is_sdxl=False,
    ):
        """
        MarkdownからPDFを作成するメソッド
        """
        html = cls.convert_md2html(
            md_content, is_plantuml=is_plantuml, is_mermaid=is_mermaid, is_sdxl=is_sdxl
        )
        # PDF生成
        pdfkit.from_string(html, output_file, configuration=cls.config)
        logger.info(f"PDF generated: {output_file}")
