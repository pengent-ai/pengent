import pytest

from mock.mock_llm_client import MockLLMClient


@pytest.fixture
def client():
    return MockLLMClient(
        "mock-model", config={"output_file_path": "../.output/test_output.txt"}
    )


def test_init(client: MockLLMClient):
    assert client.model_name == "mock-model"
    assert client.temperature == 0.0
    assert isinstance(client.config, dict)


def test_parse_json_valid(client: MockLLMClient):
    text = '{"key": "value"}'
    result = client.parse_json(text)
    assert result == {"key": "value"}


def test_parse_json_invalid_with_fallback(client: MockLLMClient):
    text = "{invalid json"
    fallback = {"fallback": True}
    result = client.parse_json(text, fallback=fallback)
    assert result == fallback
