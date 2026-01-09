from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
from ...type.rag import DocStructuredRagFormat
from ...lib import get_logger
import tiktoken


@dataclass
class Chunk:
    """チャンクデータ"""
    title: Optional[str]  # 全体のタイトル(例: ドキュメントタイトル)
    section: Optional[str]  # セクション名(例: 見出し)
    chunk_index: int  # チャンク番号
    body: str  # 本文

    def __repr__(self):
        # bodyの先頭だけ表示(最大30文字に切り詰め)
        body_preview = self.body.replace("\n", " ").strip()
        if len(body_preview) > 30:
            body_preview = body_preview[:27] + "..."
        return (
            f"Chunk(index={self.chunk_index}, "
            f"section='{self.section}', body='{body_preview}')"
        )


class ChunkerBase(ABC):
    """
    チャンクャーのベースクラス
    """
    def __init__(
        self,
        max_tokens: int = 512,
        overlap: int = 50,
        normalizer: Optional[callable] = None,
    ):
        self.logger = get_logger()
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.normalizer = normalizer
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    @abstractmethod
    def split(self, *args, **kwargs) -> List[Chunk]:
        """
        テキストをチャンク単位に分割する
        """
        pass

    def to_doc_structured_format(
        self, chunks: List[Chunk]
    ) -> List[DocStructuredRagFormat]:
        """
        チャンクをDocStructuredRagFormatに変換

        Args:
            chunks: チャンクのリスト

        Returns:
            DocStructuredRagFormatのリスト
        """
        return [
            DocStructuredRagFormat(
                title=chunk.title,
                body=chunk.body,
                section=chunk.section,
            )
            for chunk in chunks
        ]
