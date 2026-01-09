from dataclasses import dataclass, field
from typing import Optional, List
from ....lib import get_logger
from ....type.rag import SimpleFAQRagFormat
from ....type.rag_block import AnyBlock, HeadingBlock


@dataclass
class FAQPair:
    """FAQ質問・回答ペア"""

    question: str
    answer: str
    source_url: Optional[str] = None
    confidence: float = 1.0
    tags: List[str] = field(default_factory=list)


@dataclass
class FAQAnalysisConfig:
    """
    FAQ抽出設定
    """
    question_indicators: List[str] = field(
        default_factory=lambda: [
            "?",
            "？",
            "Q:",
            "質問",
            "問い",
            "疑問",
            "どうやって",
            "なぜ",
            "どのように",
            "教えて",
            # "方法", "やり方", "使い方", "設定", "インストール", "エラー", "問題"
        ]
    )
    answer_indicators: List[str] = field(
        default_factory=lambda: ["A:", "回答:", "答え:", "解決:", "対処:"]
    )
    min_answer_length: int = 10
    max_answer_length: int = 2000
    question_keywords: List[str] = field(
        default_factory=lambda: [
            "方法",
            "やり方",
            "使い方",
            "設定",
            "インストール",
            "エラー",
            "問題",
            "トラブル",
        ]
    )
    tech_keywords: List[str] = field(
        default_factory=lambda: [
            "API",
            "SDK",
            "データベース",
            "ファイル",
            "ネットワーク",
            "セキュリティ",
        ]
    )


class FAQAnalyser:
    """FAQ抽出アナライザー"""
    def __init__(
        self,
        config: Optional[FAQAnalysisConfig] = None,
        source_url: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ):
        self.config = config if config is not None else FAQAnalysisConfig()
        self.source_url: str = source_url
        self.tags: List[str] = tags or []
        self.logger = get_logger()

    def _is_valid_answer(self, answer: str) -> bool:
        """有効な回答かどうかを判定"""
        return (
            self.config.min_answer_length
            <= len(answer)
            <= self.config.max_answer_length
        )

    def _clean_question_text(self, text: str) -> str:
        """質問文をクリーンアップ"""
        # 質問インジケーターを除去
        for indicator in ["Q:", "質問:", "問い:"]:
            text = text.replace(indicator, "").strip()
        return text

    def _clean_answer_text(self, text: str) -> str:
        """回答文をクリーンアップ"""
        # 回答インジケーターを除去
        for indicator in self.config.answer_indicators:
            text = text.replace(indicator, "").strip()
        return text

    def _is_question_candidate(self, content: str, block: AnyBlock) -> bool:
        """質問候補かどうかを判定"""
        # 見出しタグは質問候補
        if isinstance(block, HeadingBlock):
            return True

        # 質問インジケーターをチェック
        for indicator in self.config.question_indicators:
            if indicator in content:
                return True
        return False

    def _generate_tags(self, question: str, answer: str) -> List[str]:
        """FAQ内容からタグを生成"""
        tags = []
        # 質問からキーワード抽出
        for keyword in self.config.question_keywords:
            if keyword in question:
                tags.append(keyword)

        # 技術的なキーワード
        tech_keywords = self.config.tech_keywords
        combined_text = f"{question} {answer}"
        for keyword in tech_keywords:
            if keyword.lower() in combined_text.lower():
                tags.append(keyword)
        return tags

    def extract_faq_pairs_from_blocks(self, blocks: List[AnyBlock]) -> List[FAQPair]:
        """
        ブロックからFAQペアを抽出(外部から利用可能)

        Args:
            blocks (List[AnyBlock]): 入力ブロックのリスト
        Returns:
            List[FAQPair]: 抽出されたFAQペアのリスト
        """
        faq_pairs: List[FAQPair] = []
        current_question = None
        current_answer_parts = []

        i = 0
        for block in blocks:
            content = block.content.strip()
            if not content:
                continue
            # 質問候補かどうかを判定
            if self._is_question_candidate(content, block):
                self.logger.debug(
                    f"Found question candidate: {i} {block.type} {content[:50]}"
                )
                i += 1

                # 既存の質問があればFAQペアを追加
                if current_question and current_answer_parts:
                    answer = "\n".join(current_answer_parts).strip()
                    if self._is_valid_answer(answer):
                        faq_pairs.append(
                            FAQPair(
                                question=current_question,
                                answer=answer,
                                source_url=self.source_url,
                                tags=self._generate_tags(current_question, answer),
                            )
                        )

                # 新しい質問を開始
                current_question = self._clean_question_text(content)
                current_answer_parts = []
            else:
                # 回答候補として追加
                if current_question:
                    cleaned_content = self._clean_answer_text(content)
                    if cleaned_content:
                        current_answer_parts.append(cleaned_content)

        # 最後の質問を処理
        if current_question and current_answer_parts:
            answer = "\n".join(current_answer_parts).strip()
            if self._is_valid_answer(answer):
                faq_pair = FAQPair(
                    question=current_question,
                    answer=answer,
                    source_url=self.source_url,
                    tags=self._generate_tags(current_question, answer),
                )
                faq_pairs.append(faq_pair)

        return faq_pairs

    def to_simple_faq_format(
        self, faq_pairs: List[FAQPair]
    ) -> List[SimpleFAQRagFormat]:
        """
        FAQペアをSimpleFAQ形式に変換

        Args:
            faq_pairs: FAQペアのリスト

        Returns:
            SimpleFAQ形式のリスト
        """
        return [
            SimpleFAQRagFormat(
                question=pair.question, answer=pair.answer, tags=pair.tags
            )
            for pair in faq_pairs
        ]
