from .vector.vectore_store_interface import VectorStoreInterface
from typing import Callable, List, Optional, Union
from .message_memory import (
    MessageMemoryBase,
    LLMMessage,
    LLMMessageRole,
    LLMMessageTool,
    MessageContentType,
)


class RetrievalMessageMemory(MessageMemoryBase):
    """RAG型メッセージ管理クラス

    概要:
        - メッセージ意味ベクトルとして保存・検索できるように拡張したクラス。
        - Retrieval-Augmented Generation(RAG)の文脈で利用され、
          履歴の中から「意味的に近い」会話を取り出して文脈に活用できる。

    UseCase:
        - 「東京の天気は？」と聞いたとき、過去に天気について話した履歴を検索して応答する
        - チャットボットがFAQ情報やドキュメントの中から意味的に近い文脈を自動取得する

    主なフロー:
        1. `add()` または `add_message()` を呼Ï出して、ベクトルストアに保存する
        2. `get_context()` でクエリをベクトル化し、意味的に近い履歴を検索して返却
        3. 検索結果は LLMMessage のリストとして呼び出し元が活用可能

        [ユーザー発言] → RetrievalMemory.add()
                ↓
        contentを埋め込み + 履歴追加

        [質問: S3料金は] → RetrievalMemory.get_context()
                ↓
        意味的に近い履歴を取得 → LLMに渡す

    課題:
        - 必要のないメッセージもベクトルに登録されるため、
          意味的に近いメッセージを検索する際にノイズが増える可能性がある。
        - 今後は登録する必要があるのか、または要約して登録するのか、などの設計が必要。
    """

    def __init__(
        self,
        vector_store: VectorStoreInterface,
        embed_fn: Callable[[str], List[float]],
        max_messages: int = 50,
    ):
        """
        ベクトルストアと埋め込み関数を用いてメッセージ履歴を初期化

        Parameters:
            vector_store (VectorStoreInterface): ベクトルストアのインスタンス
            embed_fn (Callable[[str], List[float]]): テキストをベクトルに変換する関数
            max_messages (int): メモリに保持するメッセージの最大数
        Notes:
            - embed_fnは、テキストをベクトルに変換する関数
              - 引数として文字列を受け取り、リスト形式のベクトルを返す必要があります。
            - FAQなどのタグ情報をメタデータとして持たせる
        """
        super().__init__(max_messages, _type="retrieval")
        self.vector_store = vector_store
        self.embed_fn = embed_fn

    def add(
        self,
        role: Union[str, LLMMessageRole],
        content: Optional[MessageContentType] = None,
        tool_calls: Optional[List[LLMMessageTool]] = None,
        tool_call_id: Optional[str] = None,
        is_embedding: bool = True,
    ):
        """メッセージを追加する


        embed_text は検索に使用するためのフラットなテキスト情報に変換する必要があり、
        通常は text 型の LLMMessageContent のみを対象にします。
        """
        # role を Enum に変換
        if isinstance(role, str):
            role = LLMMessageRole(role)

        # content を埋め込み対象のテキストに変換
        if isinstance(content, str):
            embed_text = content
        elif isinstance(content, list):  # List[LLMMessageContent]
            embed_text = " ".join([c.text for c in content if c.text])
        else:
            raise ValueError("content must be str or List[LLMMessageContent]")

        # ベクトルストアへ追加
        if is_embedding:
            embedding = self.embed_fn(embed_text)
            metadata = {
                "role": role.value,
                "content": embed_text,
                #   "tag": "faq"  # ← これであとで "faqだけ" と絞れる
            }
            self.vector_store.add(metadata, embedding)

        # ベースクラスにメッセージ追加(履歴用途)
        super().add(
            role=role, content=content, tool_calls=tool_calls, tool_call_id=tool_call_id
        )

    def add_message(self, message: LLMMessage, is_embedding: bool = True):
        """
        LLMMessageオブジェクトをもとに、ベクトルストアと履歴に追加する
        """
        self.add(
            role=message.role,
            content=message.content,
            tool_calls=message.tool_calls,
            tool_call_id=message.tool_call_id,
            is_embedding=is_embedding,
        )

    def get_context(self, query: str, top_k: int = 5) -> List[LLMMessage]:
        """
        クエリベクトルに基づいて、意味的に近い履歴を取得する

        Args:
            query: 検索クエリとなる自然言語文
            top_k: 最大で返す件数

        Returns:
            意味的に近い LLMMessage のリスト
        """
        query_vector = self.embed_fn(query)
        results = self.vector_store.search(query_vector, top_k=top_k)
        # タグフィルタを導入する場合 .search(query_vector, filter={"tag": "faq"})
        messages = []
        for r in results:
            try:
                role = LLMMessageRole(r["role"])
                content = str(r.get("content", ""))
                messages.append(LLMMessage(role=role, content=content))
            except Exception as e:
                print(f"[WARN] get_context: failed to parse record: {e}")
                continue

        return messages
