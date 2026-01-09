import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "src"))
)

from dotenv import load_dotenv

load_dotenv()


class TestLLMOpenAIClientIntegration:
    """OpenAI LLMクライアントの実際のAPI送信を伴うインテグレーションテスト"""

    def test_example_openai_basic_request(self):
        """example_opneai()の基本的なリクエストテスト"""
        from pengent.llm import LLMOpenAIClient

        # Arrange
        llm_client = LLMOpenAIClient(
            model_name="gpt-4o-mini",  # gpt-5-miniではなくgpt-4o-miniを使用
            temperature=0.3,
            config={
                "is_output_file": False,
                "max_tokens": 200,
                "system_prompt": "\n".join(
                    [
                        "あなたは優秀な窓口案内です。",
                        "わかりやすく、自然な日本語で丁寧に説明してください。",
                        "誤字や不自然な表現を避け、短めにまとめてください。",
                    ]
                ),
            },
        )

        # Act
        response = llm_client.request("富士山はどこの県にありますか？")

        # Assert
        assert response is not None
        assert len(str(response)) > 0
        # 富士山に関連するキーワードが含まれることを確認
        response_text = str(response).lower()
        assert any(
            keyword in response_text
            for keyword in ["静岡", "山梨", "しずおか", "やまなし"]
        )

    def test_openai_client_initialization(self):
        """OpenAIクライアントの初期化テスト"""
        from pengent.llm import LLMOpenAIClient

        # Arrange & Act
        llm_client = LLMOpenAIClient(
            model_name="gpt-4o-mini",
            temperature=0.3,
            config={
                "is_output_file": False,
                "max_tokens": 200,
            },
        )

        # Assert
        assert llm_client is not None
        assert llm_client.model_name == "gpt-4o-mini"
        assert llm_client.temperature == 0.3

    def test_openai_simple_question(self):
        """シンプルな質問のテスト"""
        from pengent.llm import LLMOpenAIClient

        # Arrange
        llm_client = LLMOpenAIClient(
            model_name="gpt-4o-mini",
            temperature=0.0,
            config={
                "is_output_file": False,
                "max_tokens": 50,
            },
        )

        # Act
        response = llm_client.request("1+1は？")

        # Assert
        assert response is not None
        assert "2" in str(response)
