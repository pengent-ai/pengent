"""
BlockChunker is a class for chunking text into blocks based on a specified block size.
for Html or Markdown
"""

from typing import List, Optional
from ..chunker_base import ChunkerBase, Chunk
from ....type.rag_block import (
    AnyBlock,
    HeadingBlock,
    TextBlock,
    CodeBlock,
    ListItemBlock,
    TableBlock,
    ImageBlock,
)


class BlockChunker(ChunkerBase):
    """
    ブロックチャンクャーの実装
    """
    def __init__(
        self,
        max_tokens: int = 512,
        overlap: int = 50,
        title: Optional[str] = None,
        heading_level: Optional[int] = None,
        normalizer: Optional[callable] = None,
    ):
        super().__init__(max_tokens=max_tokens, overlap=overlap, normalizer=normalizer)
        self.title = title
        self.heading_level = heading_level if heading_level is not None else 2

    def _chunk_section(self, section_title, blocks: List[AnyBlock]):
        text = ""
        for block in blocks:
            if isinstance(block, TextBlock):
                text += block.content + "\n"
                text += "\n"
            elif isinstance(block, CodeBlock):
                text += "```"
                if block.language:
                    text += f"{block.language}"
                text += "\n" + block.content + "\n```\n"
                text += "\n"
            elif isinstance(block, ListItemBlock):
                text += "- " + block.content
                if block.url:
                    text += f" [{block.link_text}]({block.url})"
                text += "\n"
            elif isinstance(block, TableBlock):
                header = block.rows[0]
                text += (
                    "| "
                    + " | ".join(cell if cell is not None else "" for cell in header)
                    + " |\n"
                )
                text += "| " + " | ".join(["---"] * len(header)) + " |\n"
                # data
                for row in block.rows[1:]:
                    text += (
                        "| "
                        + " | ".join(cell if cell is not None else "" for cell in row)
                        + " |\n"
                    )
                text += "\n"
            elif isinstance(block, ImageBlock):
                text += f"![{block.alt_text}]({block.url})\n"
                text += "\n"

        # Noise blocks
        if self.normalizer:
            text = self.normalizer(text)

        tokens = self.tokenizer.encode(text)
        chunks = []
        step = self.max_tokens - self.overlap

        for i in range(0, len(tokens), step):
            token_slice = tokens[i : i + self.max_tokens]
            chunk_text = self.tokenizer.decode(token_slice)
            chunks.append(
                Chunk(
                    title=self.title,
                    section=section_title,
                    chunk_index=i // step,
                    body=chunk_text,
                )
            )
        return chunks

    def split(self, blocks: List[AnyBlock]) -> List[Chunk]:
        """
        Block オブジェクトリストを見出し単位にセクション分けし、
        さらに max_tokens, overlap を見てチャンク化する
        """
        chunks = []
        section_title = "Intro"
        section_blocks = []

        for block in blocks:
            # 見出しの場合はセクションを切り替える
            if isinstance(block, HeadingBlock) and block.level <= self.heading_level:
                if section_blocks:
                    chunks.extend(self._chunk_section(section_title, section_blocks))
                # 新しいセクションを開始
                section_title = block.content
                section_blocks = [block]
            else:
                section_blocks.append(block)

        if section_blocks:
            chunks.extend(self._chunk_section(section_title, section_blocks))

        return chunks
