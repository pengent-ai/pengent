from pengent.type.llm.llm_message import (
    LLMMessage,
    LLMMessageRole,
    LLMMessageContent,
    LLMMessageContentImage,
    LLMMessageTool,
    LLMMessageToolFunction,
    LLMClientType,
)


def test_create_user_message():
    msg = LLMMessage.create_user_message("こんにちは")
    assert msg.role == LLMMessageRole.USER
    assert msg.content == "こんにちは"
    assert msg.tool_calls is None

    msg_dic = msg.to_dict()
    print(msg_dic)
    assert msg_dic["role"] == "user"
    assert msg_dic["content"] == "こんにちは"
    assert msg_dic.get("tool_calls") is None


def test_create_assistant_message():
    msg = LLMMessage.create_assistant_message("Hello!")
    assert msg.role == LLMMessageRole.ASSISTANT
    assert msg.content == "Hello!"
    assert msg.tool_calls is None

    msg_dic = msg.to_dict()
    assert msg_dic["role"] == "assistant"
    assert msg_dic["content"] == "Hello!"


def test_create_user_message_with_image():
    content = [
        LLMMessageContent.create_text_content("画像を見てください"),
        LLMMessageContent.create_image_url("https://example.com/image.jpg"),
    ]
    msg = LLMMessage.create_user_message(content)
    assert msg.role == LLMMessageRole.USER
    assert isinstance(msg.content, list)
    assert len(msg.content) == 2

    msg_dic = msg.to_dict()
    assert msg_dic["role"] == "user"
    assert len(msg_dic["content"]) == 2
    assert msg_dic["content"][0]["type"] == "text"
    assert msg_dic["content"][1]["type"] == "image"


def test_create_tools_call():
    tool = LLMMessageTool(
        id="call_123",
        function=LLMMessageToolFunction(
            name="get_weather", arguments={"location": "Tokyo"}
        ),
    )
    msg = LLMMessage.create_tools_call([tool])
    assert msg.role == LLMMessageRole.ASSISTANT
    assert msg.tool_calls is not None
    assert len(msg.tool_calls) == 1
    assert msg.tool_calls[0].function.name == "get_weather"

    msg_dic = msg.to_dict()
    assert msg_dic["role"] == "assistant"
    assert msg_dic["tool_calls"][0]["function"]["name"] == "get_weather"


def test_create_tools_result():
    msg = LLMMessage.create_tools_result("call_123", "天気は晴れです")
    assert msg.role == LLMMessageRole.TOOL
    assert msg.tool_call_id == "call_123"
    assert msg.content == "天気は晴れです"

    msg_dic = msg.to_dict()
    assert msg_dic["role"] == "tool"
    assert msg_dic["tool_call_id"] == "call_123"
    assert msg_dic["content"] == "天気は晴れです"


def test_to_dict_messages_batch():
    messages = [
        LLMMessage.create_user_message("こんにちは"),
        LLMMessage.create_assistant_message(
            "こんにちは！何か手伝えることはありますか？"
        ),
        LLMMessage.create_user_message("天気を教えて"),
    ]

    messages_dict = LLMMessage.to_dict_messages(messages)
    assert len(messages_dict) == 3
    assert messages_dict[0]["role"] == "user"
    assert messages_dict[1]["role"] == "assistant"
    assert messages_dict[2]["role"] == "user"


def test_from_dict_messages_batch():
    messages_dict = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
    ]

    messages = LLMMessage.from_dict_messages(messages_dict)
    assert len(messages) == 3
    assert messages[0].role == LLMMessageRole.USER
    assert messages[1].role == LLMMessageRole.ASSISTANT
    assert messages[2].content == "How are you?"


def test_to_format_messages_openai():
    messages = [
        LLMMessage.create_user_message("こんにちは"),
        LLMMessage.create_assistant_message("こんにちは！"),
    ]

    formatted = LLMMessage.to_format_messages(messages, LLMClientType.OPENAI)
    assert len(formatted) == 2
    assert formatted[0]["role"] == "user"
    assert formatted[1]["role"] == "assistant"


def test_to_format_messages_anthropic():
    messages = [
        LLMMessage.create_user_message("Hello"),
        LLMMessage.create_assistant_message("Hi!"),
    ]

    formatted = LLMMessage.to_format_messages(messages, LLMClientType.ANTHROPIC)
    assert len(formatted) == 2
    assert formatted[0]["role"] == "user"
    assert formatted[1]["role"] == "assistant"


def test_to_format_messages_gemini():
    messages = [
        LLMMessage.create_user_message("Hello"),
        LLMMessage.create_assistant_message("Hi!"),
    ]

    formatted = LLMMessage.to_format_messages(messages, LLMClientType.GEMINI)
    assert len(formatted) == 2
    assert formatted[0]["role"] == "user"
    assert formatted[1]["role"] == "model"
    assert "parts" in formatted[0]


def test_tool_call_format_openai():
    tool = LLMMessageTool(
        id="call_123",
        function=LLMMessageToolFunction(name="search", arguments={"query": "Python"}),
    )
    msg = LLMMessage.create_tools_call([tool])

    formatted = msg.to_format_type(LLMClientType.OPENAI)
    assert "tool_calls" in formatted
    assert formatted["tool_calls"][0]["id"] == "call_123"
    assert isinstance(formatted["tool_calls"][0]["function"]["arguments"], str)


def test_tool_result_format_anthropic():
    msg = LLMMessage.create_tools_result("call_123", "結果データ")

    formatted = msg.to_format_type(LLMClientType.ANTHROPIC)
    assert formatted["role"] == "user"
    assert formatted["content"][0]["type"] == "tool_result"
    assert formatted["content"][0]["tool_use_id"] == "call_123"


def test_message_content_image_from_data():
    image_data = b"fake_image_data"
    content = LLMMessageContentImage.create_content_image_from_data(image_data)
    assert content.base64_data is not None
    assert content.url is None
