from dataclasses import dataclass, field
from ..utility.embed.embed_base import EmbedderBase
from typing import Optional


class RgFormat:
    """
    RAGフォーマットの基底クラス
    """
    def format(self) -> dict:
        """
        フォーマットを行うメソッド
        Returns:
            dict: フォーマットされたデータ
        """
        raise NotImplementedError("This method should be overridden by subclasses.")

    def encode(self, embedder: EmbedderBase, to_numpy: bool = False):
        """
        エンコードを行うメソッド
        Args:
            embedder: ベクトル化するためのエンベッダー
        Returns:
            dict: エンコードされたデータ
        """
        raise NotImplementedError("This method should be overridden by subclasses.")


@dataclass
class SimpleFAQRagFormat(RgFormat):
    """
    シンプルFAQ RAGフォーマット
    """
    question: str
    answer: str
    tags: list[str] = field(default_factory=list)
    images: Optional[list[str]] = None
    # チャンク全体のテキスト "text" ではなく、
    # questionに対してベクトル検索(類似度検索)を行います。
    # ベクトル検索(metadata.question をベースに格納されている前提)

    def format(self) -> dict:
        """
        フォーマットを行うメソッド
        Args:
            embedder: ベクトル化するためのエンベッダー
        Returns:
            dict: フォーマットされたデータ
        """
        return {
            "text": f"Q: {self.question}\nA: {self.answer}",
            "question": self.question,
            "answer": self.answer,
            "tags": self.tags,
            "images": self.images,
        }

    def encode(self, embedder: EmbedderBase, to_numpy: bool = False):
        """
        エンコードを行うメソッド
        Args:
            embedder: ベクトル化するためのエンベッダー
        Returns:
            dict: エンコードされたデータ
        """
        return embedder.encode(self.question, to_numpy=to_numpy)

    @classmethod
    def from_dict(cls, data: dict) -> "SimpleFAQRagFormat":
        return cls(
            question=data["question"], answer=data["answer"], tags=data.get("tags", [])
        )


@dataclass
class DocStructuredRagFormat(RgFormat):
    """
    ドキュメント構造化RAGフォーマット
    """
    title: str
    body: str
    path: Optional[str] = None
    section: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    images: Optional[list[str]] = None

    def format(self) -> dict:
        return {
            "text": f"# {self.title}\n\n{self.body}",
            "title": self.title,
            "section": self.section,
            "path": self.path,
            "tags": self.tags,
            "images": self.images,
        }

    def encode(self, embedder: EmbedderBase, to_numpy: bool = False):
        """
        タイトルと本文を連結してベクトル化する。
        """
        return embedder.encode(
            f"{self.title}\n{self.section}\n{self.body}", to_numpy=to_numpy
        )
