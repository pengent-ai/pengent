import json
from pathlib import Path

PROJECT_NAME = Path(".").resolve().name
print(f"Project Name: {PROJECT_NAME}")


CODE_MAP = {
    "W291": {"message": "行末に不要な空白があります。", "severity": "🟢低"},
    "W292": {
        "message": "ファイルの最後に改行がありません。",
        "severity": "🟢低",
    },
    "E501": {
        "message": "行が長すぎます。79文字以内にしてください。",
        "severity": "🟢低",
    },
    "D101": {
        "message": "クラスにドキュメンテーション文字列がありません。",
        "severity": "⚪️無害",
    },
}


def get_relative_path(absolute_path: str) -> str:
    """
    絶対パスからプロジェクトルートからの相対パスを取得
    """
    try:
        index = absolute_path.index(PROJECT_NAME)
        return absolute_path[index + len(PROJECT_NAME) + 1 :]
    except ValueError:
        return absolute_path


class GenerateLinter:
    """Linterレポートを生成するクラス"""

    def __init__(
        self, json_file="ruff-report.json", output_file="lint-result"
    ):
        """
        初期化
        """
        self.json_file = json_file
        self.output_file = output_file

    def _genarate_lint_report(self, data: list) -> str:
        _str = ""
        if not data:
            _str += "## Linter(リンタ)指摘事項なし\n\n"
            _str += "素晴らしいコードです！🎉\n"
            return _str

        _str += "## Linter(リンタ)レビュー\n\n"
        _str += "以下の指摘事項があります。コードを見直してください。\n\n"

        _str += f"総数:{len(data)}個\n"

        _str += "### 指摘事項一覧\n"
        _str += "|コード|重要性|項目|ファイル名|行数|自動修正|\n"
        _str += "|---|---|---|---|---|---|\n"
        for issue in data:
            code = issue.get("code", "-")
            severity = (
                CODE_MAP.get(code, {}).get("severity", "❓不明")
                if code != "-"
                else "-"
            )
            message = CODE_MAP.get(code, {}).get(
                "message", issue.get("message", "-")
            )
            filename = get_relative_path(issue.get("filename", "-"))
            file_link = f"./{filename}"

            line = ""
            if issue.get("location") and issue["location"].get("row"):
                line = f"{issue['location']['row']}行目"
            if issue["location"].get("column"):
                line += f"{issue['location']['column']}列"
            if issue.get("end_location"):
                if issue["end_location"].get("row"):
                    line += f" 〜 {issue['end_location']['row']}行目"
                if issue["end_location"].get("column"):
                    line += f"{issue['end_location']['column']}列"
            auto_fix = "✅" if issue.get("fix") else "❌"

            _str += f"|{code}|{severity}|{message}|"
            _str += f"[{filename}]({file_link})|{line}|{auto_fix}|\n"

        _str += "\n\n"
        _str += "### 自動修正コマンド\n"
        _str += (
            "自動修正が可能な指摘事項については、"
            "以下のコマンドで自動修正を試みることができます。\n\n"
        )
        _str += "```bash\n"
        _str += "ruff check --fix .\n"
        _str += "```\n\n"

        return _str

    def generate_lint_report_json(self):
        with open(self.json_file, "r") as f:
            data = json.load(f)

        with open(f"{self.output_file}.md", "w") as f:
            report_body = self._genarate_lint_report(data)
            f.write(report_body)

        with open(f"{self.output_file}.json", "w") as f:
            report = {"body": self._genarate_lint_report(data)}
            json.dump(report, f, ensure_ascii=False, indent=4)

        print(
            f"Linter report generated: {self.output_file}.md"
            f" and {self.output_file}.json"
        )


if __name__ == "__main__":
    generator = GenerateLinter()
    generator.generate_lint_report_json()
