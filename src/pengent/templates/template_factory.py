import importlib.resources
from typing import Union, List
import json


def get_template_content(template_name: str) -> str:
    """
    指定されたテンプレート名の内容を取得する関数

    Args:
        template_name (str): テンプレートの名前

    Returns:
        str: テンプレートの内容
    """
    try:
        if "会議録" in template_name or "kaigiroku" in template_name:
            template_name = "tmp_kaigiroku.txt"
            template_module = "pengent.templates.bussiness"
        elif "内部ノウハウ" in template_name or "knowhow" in template_name:
            template_name = "tmp_tech_knowhow.txt"
            template_module = "pengent.templates.tech"
        elif "技術比較" in template_name or "tech_comparison" in template_name:
            template_name = "tmp_tech_comparison.txt"
            template_module = "pengent.templates.tech"
        elif "技術比較" in template_name or "tech_comparison" in template_name:
            template_name = "tmp_tech_comparison.txt"
            template_module = "pengent.templates.tech"

        else:
            raise ValueError(f"Unsupported template name: {template_name}")

        with importlib.resources.open_text(template_module, template_name) as f:
            return f.read()
    except FileNotFoundError:
        raise ValueError(
            f"Template '{template_name}' not found in the templates."
        ) from FileNotFoundError


def get_template_topics(template_name: str) -> List[Union[dict, str]]:
    """
    指定されたテンプレート名のトピック(ヒアリング用の項目)を取得する関数

    Args:
        template_name (str): テンプレートの名前

    Returns:
        List[Union[dict,str]]: トピックのリスト
    """
    try:
        template_module = "pengent.templates.hearing"
        if "WEB開発" in template_name or "website" in template_name:
            template_name = "topics_website_develop.txt"

        with importlib.resources.open_text(template_module, template_name) as f:
            return json.load(f)

    except FileNotFoundError:
        raise ValueError(
            f"Template '{template_name}' not found in the hearing templates."
        ) from FileNotFoundError
