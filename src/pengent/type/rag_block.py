from typing import List, Optional, Union, Literal
from dataclasses import dataclass, field


@dataclass
class Block:
    """
    基底ブロック
    """
    type: str
    content: str


@dataclass
class HeadingBlock(Block):
    """
    見出しブロック
    """
    type: Literal["heading"] = "heading"
    content: str = ""
    level: int = 1


@dataclass
class TextBlock(Block):
    """
    テキストブロック
    """
    type: Literal["text"] = "text"
    content: str = ""


@dataclass
class CodeBlock(Block):
    """
    コードブロック
    """
    type: Literal["code"] = "code"
    content: str = ""
    language: Optional[str] = None


@dataclass
class ListItemBlock(Block):
    """
    リストアイテムブロック
    """
    type: Literal["list_item"] = "list_item"
    content: str = ""
    url: Optional[str] = None
    link_text: Optional[str] = None


@dataclass
class TableBlock(Block):
    """
    表ブロック
    """
    type: Literal["table"] = "table"
    content: str = ""
    rows: List[List[str]] = field(default_factory=list)


@dataclass
class ImageBlock(Block):
    """
    画像ブロック
    """
    type: Literal["image"] = "image"
    content: str = ""
    url: Optional[str] = None
    alt_text: Optional[str] = None
    base64: Optional[str] = None


# Union型(全ブロックの共通型)
AnyBlock = Union[
    HeadingBlock,
    TextBlock,
    CodeBlock,
    ListItemBlock,
    TableBlock,
    ImageBlock,
]
