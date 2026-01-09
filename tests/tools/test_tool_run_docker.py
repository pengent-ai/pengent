# tests/tools/test_tool_run_docker_code.py

import pytest
from pengent.tools.tools.coder import ToolRunDockerCode


@pytest.mark.skipif(
    not ToolRunDockerCode().is_docker_available(),
    reason="Dockerが利用できないためスキップ",
)
def test_run_python_code_success():
    tool = ToolRunDockerCode()
    result = tool.run("print('Hello from Python')", language="python")

    assert result["status"] == "ok"
    assert "Hello from Python" in result["stdout"]


@pytest.mark.skipif(
    not ToolRunDockerCode().is_docker_available(),
    reason="Dockerが利用できないためスキップ",
)
def test_run_node_code_success():
    tool = ToolRunDockerCode()
    result = tool.run("console.log('Hello from Node')", language="node")
    assert result["status"] == "ok"
    assert "Hello from Node" in result["stdout"]


@pytest.mark.skipif(
    not ToolRunDockerCode().is_docker_available(),
    reason="Dockerが利用できないためスキップ",
)
def test_invalid_language():
    tool = ToolRunDockerCode()
    with pytest.raises(ValueError):
        tool.run("puts 'Hello'", language="ruby")


@pytest.mark.skipif(
    not ToolRunDockerCode().is_docker_available(),
    reason="Dockerが利用できないためスキップ",
)
def test_run_with_invalid_code():
    tool = ToolRunDockerCode()
    result = tool.run("print(Hello", language="python")  # 構文エラー

    assert result["status"] == "error" or result["status"] == "fail"


@pytest.mark.skipif(
    not ToolRunDockerCode().is_docker_available(),
    reason="Dockerが利用できないためスキップ",
)
def test_run_timeout_handling():
    tool = ToolRunDockerCode()
    result = tool.run("while True: pass", language="python")

    assert result["status"] in ("timeout", "fail")
