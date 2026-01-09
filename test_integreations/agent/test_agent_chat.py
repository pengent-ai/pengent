from pengent.core.sessions.session import Session
from pengent.agents.basic.agent_chat import AgentChat
from pengent.type.agent.agent_enum import AgentSendOutput


class TestAgentChatIntegration:
    """AgentChatの実際のAPI送信を伴うインテグレーションテスト"""

    def test_agent_run_and_send(self):
        """基本的なrun()とsend()のテスト"""
        agent = AgentChat()
        output: AgentSendOutput = agent.send("こんにちは！")

        # Assert
        assert output is not None
        assert hasattr(output, "content") or hasattr(output, "message")

    def test_agent_run_and_send_with_session(self):
        """メッセージメモリを使ったテスト"""
        # Arrange
        agent = AgentChat()
        session = Session(
            session_id="test_session_001",
            user_id="test_user_001",
        )
        output1: AgentSendOutput = agent.run(
            session=session, input="今日は天気がいいですね"
        )
        output2: AgentSendOutput = agent.run(
            session=session, input="私の前の質問は何でしたか？"
        )

        # Assert
        assert output1 is not None
        assert output2 is not None
        assert session.events is not None
        memory_dict = session.events.to_dict()
        assert isinstance(memory_dict, dict)
        # メモリに複数のメッセージが保存されていることを確認
        assert len(memory_dict) > 0

