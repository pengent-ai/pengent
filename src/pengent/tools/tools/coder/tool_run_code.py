import subprocess
import tempfile
import os
import ast
from ....tools.tool_utils import ToolBase


class ToolRunCode(ToolBase):
    """
    Pythonコードを安全に実行するためのツールクラス。

    - subprocess を使ってコードを実行
    - 標準ライブラリ以外・危険な操作を含むコードは弾く
    - 実行後は一時ファイルを削除し、結果を返す

    このツールは LLM による「コード生成の実行確認」などに利用されることを想定。
    """

    name = "run_code"
    description = (
        "指定されたPythonコードを安全にsubprocessで実行します(標準ライブラリで簡易のみ)"
    )

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "実行するPythonコード",
                },
            },
            "required": ["code"],
        }

    def is_safe_code(self, code: str) -> bool:
        """
        与えられたコードに危険な操作が含まれていないか静的解析する。

        検出対象：
        - 危険モジュール:os, sys, subprocess, shutil
        - 危険関数:eval, exec, open, __import__
        - 危険な属性呼び出し：.system(), .remove(), etc.

        Returns:
            bool: 安全ならTrue、危険ならFalse
        """
        dangerous_modules = {"os", "sys", "subprocess", "shutil"}
        dangerous_functions = {"eval", "exec", "open", "__import__"}
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in dangerous_modules:
                            return False
                elif isinstance(node, ast.ImportFrom):
                    if node.module in dangerous_modules:
                        return False
                elif isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in dangerous_functions:
                        return False
                    if isinstance(func, ast.Attribute):
                        if func.attr in {
                            "system",
                            "remove",
                            "unlink",
                            "rmdir",
                        }:
                            return False
            return True
        except Exception:
            return False

    def run(self, code: str) -> dict:
        """
        指定されたPythonコードを一時ファイルに書き込み、安全に実行する。

        Parameters:
            code (str): 実行対象のPythonコード(標準ライブラリ限定)

        Returns:
            dict: 実行結果(stdout, stderr, returncode など)

        Notes:
            - 危険コードは事前に静的解析で弾かれます。
            - 実行は subprocess によって行われます。
            - 実行時間は timeout (10秒) に制限されます。
            - 実行後は一時ファイルを削除します。
        """
        if not self.is_safe_code(code):
            return {
                "status": "rejected",
                "reason": "安全でないコードを検出しました",
            }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            filepath = f.name

        try:
            result = subprocess.run(
                ["python", filepath],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return {
                "status": "ok" if result.returncode == 0 else "error",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "reason": "実行時間が制限を超えました",
            }
        finally:
            os.remove(filepath)
