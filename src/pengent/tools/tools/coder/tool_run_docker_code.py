import subprocess
import os
from ....tools.tool_utils import ToolBase


class ToolRunDockerCode(ToolBase):
    """
    Dockerを使って任意のコードを安全に実行するツール(Python / Node.js 対応)

    - 軽量なAlpineイメージを使用(環境変数で上書き可能)
    - subprocessでdockerコマンドを実行
    - 実行後のコンテナは残りません(--rm付き)
    """

    name = "run_code_docker"
    description = "コードをDocker上で実行します(Python / Node.js対応)"
    _docker_available_cache: bool | None = None

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "実行するコード",
                },
                "language": {
                    "type": "string",
                    "enum": ["python", "node"],
                    "description": "使用する言語(pythonまたはnode)",
                },
            },
            "required": ["code", "language"],
        }

    def get_image_and_cmd(self, language: str) -> tuple[str, str]:
        """
        言語に応じたDockerイメージと実行コマンドを返す
        """
        if language == "python":
            image = os.environ.get("DOCKER_IMAGE_PYTHON", "python:3.12-alpine")
            return image, "mkdir -p /app && cat > /app/main.py && python /app/main.py"
        elif language == "node":
            image = os.environ.get("DOCKER_IMAGE_NODE", "node:20-alpine")
            return image, "mkdir -p /app && cat > /app/main.js && node /app/main.js"
        else:
            raise ValueError(f"Unsupported language: {language}")

    def is_docker_available(self) -> bool:
        """
        Dockerが実行可能かどうかを判定する

        Returns:
            bool: Dockerコマンドが利用可能ならTrue、そうでなければFalse
        """
        if self.__class__._docker_available_cache is not None:
            return self.__class__._docker_available_cache

        try:
            subprocess.run(
                [
                    "docker",
                    "info",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=True,
            )

            # 追加チェック: 実際にコンテナが起動できるかどうか簡易実行で確認
            image = os.environ.get("DOCKER_IMAGE_PYTHON", "python:3.12-alpine")
            subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    image,
                    "sh",
                    "-c",
                    "echo ok",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
                check=True,
            )
            self.__class__._docker_available_cache = True
        except Exception:
            self.__class__._docker_available_cache = False

        return self.__class__._docker_available_cache

    def run(self, code: str, language: str) -> dict:
        """
        指定されたコードを一時ファイルとして保存し、Docker上で実行する

        Parameters:
            code (str): 実行対象のコード
            language (str): 使用する言語("python" or "node")

        Returns:
            dict: 実行結果(stdout, stderr, statusなど)
        """

        # Dockerが利用可能か確認
        if not self.is_docker_available():
            return {
                "status": "unavailable",
                "reason": "Dockerが起動していないか、接続できません。",
            }

        image, cmd = self.get_image_and_cmd(language)

        try:
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-i",
                    image,
                    "sh",
                    "-c",
                    cmd,
                ],
                input=code,
                capture_output=True,
                text=True,
                timeout=15,
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
        except Exception as e:
            return {"status": "fail", "reason": str(e)}
