from unittest.mock import patch
from pengent.tools.tools.coder.tool_run_code import ToolRunCode
import subprocess


def test_run_safe_code():
    tool = ToolRunCode()
    code = "print('hello')"
    result = tool.run(code)

    assert result["status"] == "ok"
    assert "hello" in result["stdout"]
    assert result["exit_code"] == 0


def test_run_dangerous_code():
    tool = ToolRunCode()
    dangerous_code = "import os\nos.system('rm -rf /')"
    result = tool.run(dangerous_code)

    assert result["status"] == "rejected"
    assert "安全でない" in result["reason"]


def test_run_with_timeout():
    """タイムアウトのテスト（モックを使用して高速化）"""
    tool = ToolRunCode()
    infinite_loop_code = "while True: pass"

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="python", timeout=10)
        result = tool.run(infinite_loop_code)

    assert result["status"] == "timeout"
    assert "制限" in result["reason"]


def test_run_with_syntax_error():
    tool = ToolRunCode()
    broken_code = "print('hello'"
    result = tool.run(broken_code)

    assert result["status"] == "rejected"
    assert "安全でない" in result["reason"]
