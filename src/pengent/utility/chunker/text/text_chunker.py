from typing import List, Dict, Optional
import re
from ..chunker_base import ChunkerBase, Chunk


class TextChunker(ChunkerBase):
    """
    テキストチャンクャーの実装
    """
    def __init__(
        self,
        max_tokens: int = 512,
        overlap: int = 50,
        title: Optional[str] = None,
        heading_patterns: Optional[List[str]] = None,
        normalizer: Optional[callable] = None,
    ):
        super().__init__(max_tokens=max_tokens, overlap=overlap, normalizer=normalizer)
        self.heading_patterns = heading_patterns
        if not self.heading_patterns:
            # デフォルトの見出しパターン
            self.heading_patterns = [re.compile(r"^\d+\.\s.+")]
        else:
            self.heading_patterns = [
                re.compile(pattern) for pattern in heading_patterns
            ]
        self.title = title

    def _chunk_section(self, lines: list[str]) -> List[Dict[str, str]]:
        """
        セクション単位でのチャンクに分割
        Returns:
            List[Dict]: section(見出し)とtextをもつ辞書リスト
        """
        sections = []
        current = {"section": "イントロ", "text": ""}

        for line in lines:
            line = line.strip()
            if any(p.match(line) for p in self.heading_patterns or []):
                if current["text"].strip():  # 現在のセクションを保存
                    sections.append(current)
                current = {"section": line, "text": ""}
            else:
                current["text"] += line + "\n"

        if current["text"].strip():
            sections.append(current)

        return sections

    def split(self, text: str) -> List[Chunk]:
        """
        テキストをチャンク単位に分割する
        Args:
            text (str): 分割するテキスト
        Returns:
            List[str]: 分割されたテキストのリスト
        """
        if not text:
            return []

        if self.normalizer and callable(self.normalizer):
            text = self.normalizer(text)

        lines = text.splitlines()

        if not self.title:
            # 1行目をタイトルとして使用
            self.title = lines[0].strip() if lines else "No Title"

        # セクションごとに分割
        sections = self._chunk_section(lines)
        self.logger.debug(f"sections count: {len(sections)}")

        chunks = []
        for section in sections:
            tokens = self.tokenizer.encode(section["text"])
            self.logger.debug(
                f"section: {section['section']}, tokens count: {len(tokens)}"
            )
            for i in range(0, len(tokens), self.max_tokens - self.overlap):
                chunk_tokens = tokens[i : i + self.max_tokens]
                chunk_text = self.tokenizer.decode(chunk_tokens)
                chunks.append(
                    Chunk(
                        title=self.title,
                        section=section["section"],
                        chunk_index=i // (self.max_tokens - self.overlap),
                        body=chunk_text,
                    )
                )
        return chunks
